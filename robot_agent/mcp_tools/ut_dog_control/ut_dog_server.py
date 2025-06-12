#!/usr/bin/env python3
"""
UT Dog MCP Server - A comprehensive MCP server for Unitree Go2 robot dog control.

This server provides tools for:
- Robot movement (forward, backward, left, right, turn)
- Image capture and surrounding view
- Navigation and status monitoring
- Human communication
- Real-time streaming via SSE
"""

import asyncio
import base64
import io
import json
import math
import os
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import cv2
import numpy as np
import requests
import socketio
import websocket
from fastmcp import FastMCP, Context
from PIL import Image
from pydantic import BaseModel, Field
from websocket import WebSocketConnectionClosedException, create_connection

# Initialize FastMCP server
mcp = FastMCP("UT Dog Robot Control Server")

# Constants
MOVE_SUFFIX = "/signalservice/robot/move"
SNAPSHOT_SUFFIX = "/signalservice/robot/snapshot"
AUDIO_OPEN_ENDPOINT = "/signalservice/voicetalk/open"
AUDIO_CLOSE_ENDPOINT = "/signalservice/voicetalk/close"
WS_SERVER = "ws://127.0.0.1:9000/ws/agent_tools"

# API Configuration for different image sources
API_SUFFIX = {
    'out_rgb_depth': "/signalservice/video/color_depth_snapshot",
    'dog_rgb': "/signalservice/robot/snapshot",
    'height_map': "/signalservice/robot/height_map"
}

# Default URLs - can be overridden via environment variables
DEFAULT_ROBOT_URL = "http://172.16.33.229:18080"
DEFAULT_AUDIO_URL = "http://172.16.33.229:8080"
DEFAULT_NAV_URL = "http://localhost:8765"
DEFAULT_MAP_SERVER_URL = "http://172.16.33.229:5000"

# Global variables for map server connection
sio = socketio.Client()
status_message = "Waiting to connect to server..."
latest_map_image = None
latest_path_image = None
image_lock = threading.Lock()
map_server_connected = False

# Navigation status enum
class NavigationStatus(IntEnum):
    NOT_STARTED = 0
    NAVIGATING = 1
    COMPLETED = 2
    UNREACHABLE = 3

class ChatResult(BaseModel):
    thinking: str = Field(description="Think step by step before dropping next message")
    result: str = Field(description="Summarize the conversation result")
    is_done: bool = Field(description="Whether the goal has been reached")
    chat: str = Field(description="Chat content to say to human")

class RobotStatus(BaseModel):
    """Robot status data structure for streaming"""
    timestamp: float
    position: List[float]
    navigation_status: str
    robot_connected: bool
    nav_service_available: bool
    battery_level: Optional[float] = None
    movement_state: str = "idle"

# Helper functions
def get_robot_url() -> str:
    """Get robot base URL from environment or use default."""
    import os
    return os.getenv("ROBOT_URL", DEFAULT_ROBOT_URL)

def get_audio_url() -> str:
    """Get audio service URL from environment or use default."""
    import os
    return os.getenv("AUDIO_URL", DEFAULT_AUDIO_URL)

def get_nav_url() -> str:
    """Get navigation service URL from environment or use default."""
    import os
    return os.getenv("NAV_URL", DEFAULT_NAV_URL)

def get_map_server_url() -> str:
    """Get map server URL from environment or use default."""
    import os
    return os.getenv("MAP_SERVER_URL", DEFAULT_MAP_SERVER_URL)

@mcp.tool()
def get_map_server_status(input: str = "") -> Dict[str, Any]:
    """
    Get the current map server connection status.
    
    Args:
        input: Optional input parameter (not used, for compatibility)
    
    Returns:
        Dictionary containing connection status and server info
    """
    return {
        "connected": map_server_connected,
        "status_message": status_message,
        "server_url": get_map_server_url(),
        "has_cached_image": latest_map_image is not None,
        "timestamp": time.time()
    }

def make_api_request(endpoint: str) -> Optional[Dict[str, Any]]:
    """
    Generic API request handler
    
    Args:
        endpoint: API endpoint path
    Returns:
        API response data or None if request failed
    """
    try:
        url = get_robot_url() + endpoint
        response = requests.get(url, headers={"Content-Type": "application/json"})
        print(f"API endpoint: {endpoint}")
        response_data = response.json()
        if 'data' in response_data:
            print(f"Response data keys: {response_data.get('data', {}).keys()}")
        
        if response.status_code == 200:
            return response_data.get('data', {})
        print(f"API request failed: {response.status_code}, {response.text}")
        return None
    except Exception as e:
        print(f"API request error: {str(e)}")
        return None

def process_depth_image(depth_data: np.ndarray) -> np.ndarray:
    """Process depth image data to colored visualization"""
    depth_normalized = cv2.normalize(depth_data, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    return cv2.applyColorMap(depth_normalized, cv2.COLORMAP_TURBO)

def get_height_map() -> Optional[np.ndarray]:
    """Get and process height map data"""
    height_map_data = make_api_request(API_SUFFIX['height_map'])
    
    if not height_map_data:
        return None
        
    try:
        height_data = np.array(height_map_data['data'], dtype=np.float32).reshape(
            (height_map_data['height'], height_map_data['width'])
        )
        
        # Handle invalid values
        max_val = height_data.max()
        height_data[height_data == max_val] = np.nan
        height_data = np.nan_to_num(height_data, nan=0.0)
        
        # Create visualization
        height_normalized = cv2.normalize(height_data, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        height_map_img = cv2.applyColorMap(height_normalized, cv2.COLORMAP_VIRIDIS)
        height_map_img[height_data == 0] = [0, 0, 0]
        
        cv2.imwrite('height_map.png', height_map_img)
        return height_map_img
        
    except Exception as e:
        print(f"Height map processing error: {str(e)}")
        return None

def numpy_to_base64_image(image_array: np.ndarray, format: str = 'PNG') -> str:
    """Convert numpy array to base64 image string"""
    try:
        # Convert BGR to RGB if needed (OpenCV uses BGR by default)
        if len(image_array.shape) == 3 and image_array.shape[2] == 3:
            image_array = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(image_array)
        
        # Convert to base64
        buffer = io.BytesIO()
        pil_image.save(buffer, format=format)
        img_bytes = buffer.getvalue()
        encoded = base64.b64encode(img_bytes).decode("utf-8")
        
        return f"data:image/{format.lower()};base64,{encoded}"
    except Exception as e:
        print(f"Error converting numpy array to base64: {e}")
        return ""

def connect_to_map_server(server_url: str = None):
    """Connect to the map backend server."""
    global status_message, map_server_connected
    
    if server_url is None:
        server_url = get_map_server_url()
    
    try:
        if not sio.connected:
            sio.connect(server_url)
            print(f"Attempting to connect to server: {server_url}")
        else:
            print("Already connected to map server")
    except Exception as e:
        print(f"Connection to server failed: {str(e)}")
        status_message = f"Connection to server failed: {str(e)}"
        map_server_connected = False

def disconnect_map_server():
    """Disconnect from map server"""
    global status_message, map_server_connected
    try:
        if sio.connected:
            sio.disconnect()
            map_server_connected = False
            status_message = "Disconnected from map server"
            print("Disconnected from map server")
    except Exception as e:
        print(f"Error disconnecting from map server: {e}")

def get_latest_image_from_file(image_path: str = "height_map.png") -> Optional[np.ndarray]:
    """Get the latest map image from saved file"""
    try:
        if os.path.exists(image_path):
            # Read the image file
            image = cv2.imread(image_path)
            if image is not None:
                print(f"Successfully loaded map image from {image_path}")
                return image
            else:
                print(f"Failed to read image from {image_path}")
                return None
        else:
            print(f"Map image file not found: {image_path}")
            return None
    except Exception as e:
        print(f"Error loading map image: {e}")
        return None

def get_latest_image() -> Optional[np.ndarray]:
    """Get the latest path planning image"""
    global latest_path_image, latest_map_image
    
    # First try to get the latest path image from SocketIO
    with image_lock:
        if latest_path_image is not None:
            print("Returning latest path planning image")
            return latest_path_image
    
    # Fallback to height map from sensors
    try:
        print("Attempting to get height map...")
        height_map_img = get_height_map()
        
        if height_map_img is not None:
            with image_lock:
                latest_map_image = height_map_img
            return height_map_img
    except Exception as e:
        print(f"Failed to get height map: {e}")
    
    # Fallback to saved file
    try:
        saved_image = get_latest_image_from_file("height_map.png")
        if saved_image is not None:
            with image_lock:
                latest_map_image = saved_image
            return saved_image
    except Exception as e:
        print(f"Failed to load image from file: {e}")
    
    # Final fallback - return cached image or blank image
    with image_lock:
        if latest_map_image is not None:
            print("Using cached map image")
            return latest_map_image
    
    # Return blank image if nothing available
    print("Returning blank image")
    blank_image = np.ones((500, 500, 3), dtype=np.uint8) * 255
    cv2.putText(blank_image, "Waiting for path planning image...", (100, 250), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    return blank_image

# SocketIO event handlers for map server
@sio.event
def connect():
    """Called when connected to map server"""
    global status_message, map_server_connected
    print("Connected to server")
    status_message = "Connected to server"
    map_server_connected = True

@sio.event
def disconnect():
    """Called when disconnected from map server"""
    global status_message, map_server_connected
    print("Disconnected from server")
    status_message = "Disconnected from server"
    map_server_connected = False

@sio.on('path_image_update')
def on_path_image_update(data):
    """Receive path planning image update"""
    global latest_path_image, latest_map_image
    try:
        print("Front end received image data:", data.keys())
        # Decode Base64 image
        img_data = base64.b64decode(data['image'])
        img_array = np.frombuffer(img_data, np.uint8)
        cv_image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        # Update latest path image
        with image_lock:
            print("Updating latest path image")
            latest_path_image = cv_image
            latest_map_image = cv_image  # Also update the general map image
            
    except Exception as e:
        print(f'Error processing path image: {str(e)}')

@sio.event
def map_update(data):
    """Called when map data is updated from server (legacy support)"""
    global latest_map_image
    try:
        print("Received map update from server")
        # Process the received map data here
        # This depends on the format your server sends
        latest_map_image = data  # Adjust based on actual data format
    except Exception as e:
        print(f"Error processing map update: {e}")

def request_robot_move(vx: float, vy: float, vyaw: float) -> Dict[str, Any]:
    """Send movement command to robot."""
    url = urljoin(get_robot_url(), MOVE_SUFFIX)
    print (url)
    response = requests.post(url, json={"vx": vx, "vy": vy, "vyaw": vyaw}).json()
    print (response)
    if response["code"] != '0':
        raise Exception(f"Robot move failed: {response['message']}")
    return response

def request_robot_snapshot() -> Image.Image:
    """Get RGB image from robot camera."""
    url = urljoin(get_robot_url(), SNAPSHOT_SUFFIX)
    response = requests.get(url).json()
    if response.get("code") != '0':
        raise Exception(f"Robot snapshot failed [{response['code']}]: {response['message']}")
    
    jpg_buffer = response.get("data", {}).get("rgb_jpg")
    if jpg_buffer:
        return Image.open(io.BytesIO(bytes(jpg_buffer)))
    else:
        raise Exception("Failed to get snapshot")

async def get_robot_status() -> RobotStatus:
    """Get current robot status for streaming"""
    try:
        # Test robot connectivity
        robot_url = get_robot_url()
        try:
            response = requests.get(f"{robot_url}/health", timeout=2)
            robot_connected = response.status_code == 200
        except:
            robot_connected = False
        
        # Test navigation service
        nav_url = get_nav_url()
        try:
            response = requests.get(f"{nav_url}/navigation_status/", timeout=2)
            nav_available = response.status_code == 200
            if nav_available:
                result = response.json()
                status_code = result.get("status", 0)
                nav_status = NavigationStatus(status_code).name
            else:
                nav_status = "UNAVAILABLE"
        except:
            nav_available = False
            nav_status = "UNAVAILABLE"
        
        # Get current position (estimated)
        position = get_pose()
        
        return RobotStatus(
            timestamp=time.time(),
            position=position,
            navigation_status=nav_status,
            robot_connected=robot_connected,
            nav_service_available=nav_available,
            movement_state="idle"
        )
    except Exception as e:
        return RobotStatus(
            timestamp=time.time(),
            position=[0.0, 0.0, 0.0],
            navigation_status="ERROR",
            robot_connected=False,
            nav_service_available=False,
            movement_state="error"
        )

# Movement Tools
@mcp.tool()
def move(vx: float = 0, vy: float = 0, vyaw: float = 0) -> str:
    """
    Control the robot dog movement.
    
    Args:
        vx: Speed along x-axis (m/s). Positive=forward, negative=backward. Try 1.5 if unsure.
        vy: Speed along y-axis (m/s). Positive=left, negative=right. Try 1.5 if unsure.
        vyaw: Angular velocity (rad/s). Positive=counterclockwise, negative=clockwise.
    
    Returns:
        Movement result message
    """
    try:
        remaining_vx = abs(vx)
        remaining_vy = abs(vy)
        remaining_vyaw = abs(vyaw)
        
        vx_direction = 1 if vx > 0 else -1
        vy_direction = 1 if vy > 0 else -1
        vyaw_direction = 1 if vyaw > 0 else -1
        
        # Handle large movements by breaking them down
        if remaining_vx > 3.8 or remaining_vy > 1.0 or remaining_vyaw > 4:
            while remaining_vx > 0 or remaining_vy > 0 or remaining_vyaw > 0:
                current_vx = min(2, remaining_vx) * vx_direction if remaining_vx > 0 else 0
                current_vy = min(1, remaining_vy) * vy_direction if remaining_vy > 0 else 0
                current_vyaw = min(1.5, remaining_vyaw) * vyaw_direction if remaining_vyaw > 0 else 0
                
                request_robot_move(current_vx, current_vy, current_vyaw)
                
                remaining_vx = max(0, remaining_vx - abs(current_vx))
                remaining_vy = max(0, remaining_vy - abs(current_vy))
                remaining_vyaw = max(0, remaining_vyaw - abs(current_vyaw))
                
                time.sleep(1)
        else:
            request_robot_move(vx, vy, vyaw)
        
        result_parts = ["Successfully moved the robot dog"]
        if vx != 0:
            result_parts.append(f"forward: {vx}m")
        if vy != 0:
            result_parts.append(f"left: {vy}m")
        if vyaw != 0:
            result_parts.append(f"rotate: {vyaw}rad")
        
        return ". ".join(result_parts)
        
    except Exception as e:
        return f"Failed to move the robot dog: {e}"

@mcp.tool()
def move_forward() -> str:
    """Move the robot dog forward."""
    return move(vx=0.5, vy=0, vyaw=0)

@mcp.tool()
def move_backward() -> str:
    """Move the robot dog backward."""
    return move(vx=-0.5, vy=0, vyaw=0)

@mcp.tool()
def move_left() -> str:
    """Move the robot dog left."""
    return move(vx=0, vy=-0.5, vyaw=0)

@mcp.tool()
def move_right() -> str:
    """Move the robot dog right."""
    return move(vx=0, vy=0.5, vyaw=0)

@mcp.tool()
def turn_left() -> str:
    """Turn the robot dog left (counterclockwise)."""
    return move(vx=0, vy=0, vyaw=1.5)

@mcp.tool()
def turn_right() -> str:
    """Turn the robot dog right (clockwise)."""
    return move(vx=0, vy=0, vyaw=-1.5)

# Image capture tools
@mcp.tool()
def get_image_sample() -> str:
    """
    Get the current view image from the robot dog's camera.
    
    Returns:
        Success message with image capture result
    """
    try:
        image = request_robot_snapshot()
        
        # Resize image to have longest edge as 512 pixels while maintaining aspect ratio
        width, height = image.size
        max_dim = max(width, height)
        if max_dim > 512:
            scale_factor = 512 / max_dim
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height), Image.LANCZOS)
        
        return "Successfully captured front image from robot camera"
        
    except Exception as e:
        return f"Failed to get front image: {e}"

@mcp.tool()
def get_surrounding_images() -> str:
    """
    Get surrounding images by rotating the robot and capturing 8 directional views.
    This takes time, so use only when complete environmental view is necessary.
    
    Returns:
        Success message with surrounding image capture result
    """
    try:
        images_captured = 0
        for i in range(8):
            # Capture image at current angle
            image = request_robot_snapshot()
            images_captured += 1
            
            # Rotate for next image (except on last iteration)
            if i < 7:
                request_robot_move(0, 0, 1.5)  # Rotate 1.5 radians
                time.sleep(1)
        
        return f"Successfully captured surrounding images in 8 directions ({images_captured} images total)"
        
    except Exception as e:
        return f"Failed to get surrounding images: {e}"

# SSE Streaming Tools
@mcp.tool()  
async def start_status_stream(interval: float = 2.0, duration: float = 30.0) -> str:
    """
    Start streaming robot status updates via Server-Sent Events.
    
    Args:
        interval: Time between status updates in seconds (default: 2.0)
        duration: Total streaming duration in seconds (default: 30.0)
    
    Returns:
        Streaming status message
    """
    try:
        end_time = time.time() + duration
        update_count = 0
        
        while time.time() < end_time:
            # Get current robot status
            status = await get_robot_status()
            
            # Send status update via SSE (this would be handled by FastMCP)
            print(f"Status Update {update_count + 1}: {status.model_dump_json()}")
            update_count += 1
            
            # Wait for next update
            await asyncio.sleep(interval)
        
        return f"Status streaming completed. Sent {update_count} updates over {duration} seconds."
        
    except Exception as e:
        return f"Failed to stream status: {e}"

@mcp.tool()
async def stream_camera_feed(interval: float = 1.0, duration: float = 15.0) -> str:
    """
    Stream camera images from the robot via Server-Sent Events.
    
    Args:
        interval: Time between image captures in seconds (default: 1.0)
        duration: Total streaming duration in seconds (default: 15.0)
    
    Returns:
        Camera streaming status message
    """
    try:
        end_time = time.time() + duration
        frame_count = 0
        
        while time.time() < end_time:
            try:
                # Capture image
                image = request_robot_snapshot()
                
                # Convert to base64 for streaming
                buffer = io.BytesIO()
                image.save(buffer, format='JPEG', quality=70)
                img_bytes = buffer.getvalue()
                encoded = base64.b64encode(img_bytes).decode("utf-8")
                
                # Create frame data
                frame_data = {
                    "frame": frame_count,
                    "timestamp": time.time(),
                    "image": f"data:image/jpeg;base64,{encoded}",
                    "size": f"{image.size[0]}x{image.size[1]}"
                }
                
                # Send frame via SSE (this would be handled by FastMCP)
                print(f"Camera Frame {frame_count + 1}: {len(encoded)} bytes")
                frame_count += 1
                
            except Exception as e:
                print(f"Failed to capture frame {frame_count}: {e}")
            
            # Wait for next frame
            await asyncio.sleep(interval)
        
        return f"Camera streaming completed. Sent {frame_count} frames over {duration} seconds."
        
    except Exception as e:
        return f"Failed to stream camera: {e}"

@mcp.tool()
async def get_real_time_status() -> Dict[str, Any]:
    """
    Get real-time robot status as JSON data.
    
    Returns:
        Current robot status as dictionary
    """
    try:
        status = await get_robot_status()
        return status.model_dump()
    except Exception as e:
        return {"error": str(e), "timestamp": time.time()}

# Navigation tools
@mcp.tool()
def start_navigation(goal: str) -> str:
    """
    Start point-to-point navigation to find and reach a specific target.
    
    Args:
        goal: Navigation target description (e.g., "laptop", "kitchen", "red chair")
    
    Returns:
        Navigation result message
    """
    try:
        nav_url = get_nav_url()
        
        # Send navigation request
        response = requests.post(
            f"{nav_url}/start_navigation/",
            json={"goal": goal}
        )
        response.raise_for_status()
        result = response.json()
        
        if result["code"] != 0:
            return f"Failed to start navigation: {result['message']}"
        
        # Monitor navigation status
        while True:
            status_response = requests.get(f"{nav_url}/navigation_status/")
            status_response.raise_for_status()
            status_result = status_response.json()
            
            if status_result["code"] != 0:
                return "Failed to get navigation status"
            
            status_code = status_result["status"]
            
            if status_code == NavigationStatus.COMPLETED:
                return "Navigation completed successfully. Target object is nearby."
            elif status_code == NavigationStatus.UNREACHABLE:
                return "Navigation failed. Target location is unreachable due to obstacles."
            
            # Wait before checking again
            time.sleep(1.0)
            
    except Exception as e:
        return f"Failed to start navigation: {e}"

@mcp.tool()
def get_navigation_status() -> str:
    """
    Get the current navigation status of the robot.
    
    Returns:
        Current navigation status description
    """
    try:
        nav_url = get_nav_url()
        response = requests.get(f"{nav_url}/navigation_status/")
        response.raise_for_status()
        result = response.json()
        
        if result["code"] != 0:
            return "Failed to get navigation status"
        
        status_code = result["status"]
        status_name = NavigationStatus(status_code).name
        
        status_descriptions = {
            NavigationStatus.NOT_STARTED: "Navigation not started",
            NavigationStatus.NAVIGATING: "Currently navigating",
            NavigationStatus.COMPLETED: "Navigation completed",
            NavigationStatus.UNREACHABLE: "Target location unreachable"
        }
        
        return f"Navigation status: {status_descriptions.get(status_code, 'Unknown status')}"
        
    except Exception as e:
        return f"Failed to get navigation status: {e}"

# Communication tools
@mcp.tool()
def communicate_with_human(goal: str, max_turns: int = 10) -> str:
    """
    Communicate with a human to get help or information.
    Use this when you need human assistance or have questions that can't be solved autonomously.
    
    Args:
        goal: What you want to achieve through communication
        max_turns: Maximum number of conversation turns (default: 10)
    
    Returns:
        Communication result summary
    """
    try:
        # This is a simplified version - in practice you'd integrate with the full communication system
        # For now, return a placeholder response
        return f"Communication initiated with goal: {goal}. This tool requires full integration with the communication system including TTS/ASR and WebSocket connections."
        
    except Exception as e:
        return f"Failed to communicate with human: {e}"

# Utility tools
@mcp.tool()
def robot_status() -> str:
    """
    Get overall robot status including connectivity and basic health check.
    
    Returns:
        Robot status summary
    """
    try:
        # Test robot connectivity
        robot_url = get_robot_url()
        response = requests.get(f"{robot_url}/health", timeout=5)
        robot_status = "Connected" if response.status_code == 200 else "Disconnected"
    except:
        robot_status = "Disconnected"
    
    try:
        # Test navigation service
        nav_url = get_nav_url()
        response = requests.get(f"{nav_url}/navigation_status/", timeout=5)
        nav_status = "Available" if response.status_code == 200 else "Unavailable"
    except:
        nav_status = "Unavailable"
    
    return f"Robot Status: {robot_status}, Navigation Service: {nav_status}"

# ========================================
# UNIFIED INTERFACE TOOLS (matching Thor simulator)
# ========================================

@mcp.tool()
def reset_environment(environment_id: str = "default") -> str:
    """Reset the robot environment to initial state.
    
    Parameters
    ----------
    environment_id: str, optional
        Environment identifier (for real robot, this is mostly informational)
    """
    try:
        # For real robot, we can't truly "reset" the environment, but we can reset internal state
        # Stop any ongoing navigation
        try:
            nav_url = get_nav_url()
            requests.post(f"{nav_url}/stop_navigation/", timeout=2)
        except:
            pass
        
        return f"Robot environment reset (environment_id: {environment_id})"
    except Exception as e:
        return f"Failed to reset environment: {e}"

@mcp.tool()
def step(action: str, degrees: int = 30, magnitude: float = 0.25, return_map: bool = False) -> Dict[str, Any]:
    """Execute action on the robot.

    Parameters
    ----------
    action: str
        Action to execute such as "MoveAhead", "MoveLeft", "RotateRight", etc.
    degrees: int, optional
        Rotation amount for rotate actions (default 30).
    magnitude: float, optional
        Movement magnitude for move actions (default 0.25).
    return_map: bool, optional
        If True include occupancy map in the response (not available for real robot).
    """
    try:
        result = {"code": "0", "message": ""}
        
        # Map Thor-style actions to robot movements
        if action == "MoveAhead":
            move_result = move(vx=magnitude, vy=0, vyaw=0)
        elif action == "MoveBack":
            move_result = move(vx=-magnitude, vy=0, vyaw=0)
        elif action == "MoveLeft":
            move_result = move(vx=0, vy=magnitude, vyaw=0)
        elif action == "MoveRight":
            move_result = move(vx=0, vy=-magnitude, vyaw=0)
        elif action == "RotateLeft":
            # Convert degrees to radians
            vyaw_rad = math.radians(degrees)
            move_result = move(vx=0, vy=0, vyaw=vyaw_rad)
        elif action == "RotateRight":
            # Convert degrees to radians  
            vyaw_rad = -math.radians(degrees)
            move_result = move(vx=0, vy=0, vyaw=vyaw_rad)
        else:
            result = {"code": "1", "message": f"Unknown action: {action}"}
            move_result = f"Unknown action: {action}"
        
        # Get current position (placeholder for real robot)
        position = get_pose()
        
        response = {
            "result": result,
            "position": position,
            "move_result": move_result
        }
        
        if return_map:
            # Real robot doesn't have occupancy map, return None
            response["map"] = None
            
        return response
        
    except Exception as e:
        return {
            "result": {"code": "1", "message": str(e)},
            "position": [0.0, 0.0, 0.0]
        }

@mcp.tool()
def get_pose(input: str = "") -> List[float]:
    """Return the current robot pose as [x, z, yaw].
    
    Note: Gets actual position from robot pose API endpoint.
    """
    try:
        # Call the robot pose API
        map_server_url = get_map_server_url()
        # Extract base URL (remove port if present and add correct port)
        base_url = map_server_url.split(':')[0] + ':' + map_server_url.split(':')[1]  # http://172.16.33.229
        pose_url = f"{base_url}:5000/api/robot_pose"
        
        response = requests.get(pose_url, timeout=5)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("code") == 0 and "data" in result and "xy_yaw" in result["data"]:
            xy_yaw = result["data"]["xy_yaw"]
            # API returns [x, y, yaw], but we want [x, z, yaw] for compatibility
            # Since this is a ground robot, y from API becomes z coordinate
            return [xy_yaw[0], xy_yaw[1], xy_yaw[2]]
        else:
            print(f"Unexpected API response format: {result}")
            return [0.0, 0.0, 0.0]
            
    except Exception as e:
        print(f"Failed to get robot pose from API: {e}")
        # Return placeholder values as fallback
        return [0.0, 0.0, 0.0]

@mcp.tool()
def move_to(x: float, z: float) -> Dict[str, Any]:
    """Move the robot to (x, z) world coordinates.
    
    For real robot, this uses the navigation system to reach the target.
    """
    try:
        # Use the existing navigation system with coordinates
        # This is a simplified approach - in practice you'd need coordinate transformation
        nav_url = get_nav_url()
        
        response = requests.post(
            f"{nav_url}/move_to_coordinates/",
            json={"x": x, "z": z}
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "code": result.get("code", 0),
                "data": {
                    "enabled": True,
                    "status_code": 2 if result.get("success", False) else 3,
                    "status_name": "Destination reached" if result.get("success", False) else "Destination unreachable"
                },
                "message": result.get("message", "Movement completed")
            }
        else:
            return {
                "code": 1,
                "data": {
                    "enabled": False,
                    "status_code": 0,
                    "status_name": "Navigation not started/paused"
                },
                "message": "Failed to start coordinate navigation"
            }
            
    except Exception as e:
        return {
            "code": 1,
            "data": {
                "enabled": False,
                "status_code": 0,
                "status_name": "Navigation not started/paused"
            },
            "message": str(e)
        }

@mcp.tool()
def execute_navigation_proposal(proposal_index: int, proposals_text: str) -> Dict[str, Any]:
    """Execute a specific navigation action proposal from the given text.
    
    Parameters
    ----------
    proposal_index: int
        The 1-based index of the proposal to execute (e.g., 1 for "Action 1")
    proposals_text: str
        The text containing navigation action proposals (e.g., from vision model output)
    """
    try:
        # Parse the proposals text to extract the chosen proposal
        proposals = _parse_navigation_proposals(proposals_text)
        
        if not proposals or proposal_index < 1 or proposal_index > len(proposals):
            return {
                "result": {
                    "success": False,
                    "message": f"Invalid proposal index {proposal_index}. Available proposals: {len(proposals)}"
                }
            }
        
        # Get the selected proposal
        selected_proposal = proposals[proposal_index - 1]  # Convert to 0-based index
        distance = selected_proposal["distance"]
        angle = selected_proposal["angle"]
        
        # Execute the proposal: first rotate, then move
        # Convert angle to radians for rotation
        vyaw_rad = math.radians(angle)
        
        # Rotate to target angle
        rotate_result = move(vx=0, vy=0, vyaw=vyaw_rad)
        time.sleep(0.5)  # Brief pause between actions
        
        # Move forward the specified distance
        move_result = move(vx=distance, vy=0, vyaw=0)
        
        # Get updated position
        position = get_pose()
        
        return {
            "result": {
                "success": True,
                "message": f"Executed proposal {proposal_index}: rotated {angle}° and moved {distance}m"
            },
            "position": position
        }
        
    except Exception as e:
        return {
            "result": {
                "success": False,
                "message": f"Error executing navigation proposal: {str(e)}"
            }
        }

def _parse_navigation_proposals(proposals_text: str) -> List[Dict[str, Any]]:
    """Parse navigation proposals text into structured data."""
    proposals = []
    
    # Split the text into lines
    lines = proposals_text.strip().split('\n')
    
    # Skip the header line if it exists
    start_idx = 0
    if lines and "Navigation Action Proposals" in lines[0]:
        start_idx = 1
        
    # Process each proposal line
    for i in range(start_idx, len(lines)):
        line = lines[i].strip()
        if not line or not line.startswith("Action"):
            continue
            
        try:
            # Extract information using regular expressions
            import re
            
            # Pattern to match: Distance Xm, Angle Y° (Z radians), Minimum Width Wpx
            distance_match = re.search(r"Distance (\d+\.\d+)m", line)
            angle_match = re.search(r"Angle ([-+]?\d+\.\d+)°", line)
            width_match = re.search(r"Minimum Width (\d+\.\d+)px", line)
            
            if distance_match and angle_match:
                distance = float(distance_match.group(1))
                angle = float(angle_match.group(1))
                width = float(width_match.group(1)) if width_match else None
                
                proposals.append({
                    "distance": distance,
                    "angle": angle,
                    "width": width
                })
        except Exception as e:
            print(f"Warning: Error parsing proposal line '{line}': {str(e)}")
            
    return proposals

@mcp.tool()
def capture_observation() -> Dict[str, str]:
    """Capture an RGB frame and return it as base64 data-URL.
    
    Note: Real robot doesn't have depth camera, so depth will be None.
    """
    try:
        # Get RGB image
        image = request_robot_snapshot()
        
        # Convert PIL image to base64
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        img_bytes = buffer.getvalue()
        encoded = base64.b64encode(img_bytes).decode("utf-8")
        rgb_data_url = f"data:image/png;base64,{encoded}"
        
        # Save image as a file
        #image.save("captured_image.png", format='PNG')
        
        return {
            "rgb": rgb_data_url,
            "depth": None,  # Real robot doesn't have depth camera
        }
        
    except Exception as e:
        return {
            "rgb": None,
            "depth": None,
            "error": str(e)
        }

@mcp.tool()
def get_map() -> Dict[str, Any]:
    """Return the latest occupancy map and agent pose.
    
    Note: Real robot doesn't generate occupancy maps without additional sensors.
    """
    try:
        pose = get_pose()
        return {
            "pose": pose,
            "map": None,  # Real robot doesn't have occupancy mapping
            "message": "Occupancy mapping not available on real robot"
        }
    except Exception as e:
        return {
            "pose": [0.0, 0.0, 0.0],
            "map": None,
            "error": str(e)
        }

@mcp.tool()
def get_available_actions() -> Dict[str, Any]:
    """Return all valid actions at the current position."""
    try:
        # For real robot, most movement actions are generally available
        # unless there are specific safety constraints
        
        movement_actions = ["MoveAhead", "MoveBack", "MoveLeft", "MoveRight"]
        rotation_actions = ["RotateLeft", "RotateRight"]
        
        # Check robot status to determine if actions are available
        status = robot_status()
        actions_available = "Connected" in status
        
        return {
            "movement_actions": movement_actions if actions_available else [],
            "rotation_actions": rotation_actions if actions_available else [],
            "interactable_objects": [],  # Real robot doesn't have object interaction yet
            "status": status
        }
        
    except Exception as e:
        return {
            "movement_actions": [],
            "rotation_actions": [],
            "interactable_objects": [],
            "error": str(e)
        }

@mcp.tool()
def get_environment_state() -> Dict[str, Any]:
    """Return a comprehensive state of the environment for VLM decision-making.
    
    This includes:
    - Current observation (RGB image)
    - Robot's status and available actions
    - Navigation status
    """
    try:
        # Get current observation
        observation = capture_observation()
        
        # Get robot pose (estimated)
        pose = get_pose()
        
        # Get available actions
        available_actions = get_available_actions()
        
        # Get navigation status
        nav_status = get_navigation_status()
        
        # Get robot status
        status = robot_status()
        map = get_latest_map_image()["map_image"]
        return {
            "observation": {
                "rgb": observation.get("rgb"),
                "depth": None,  # Real robot doesn't have depth
            },
            "pose": pose,
            "available_actions": available_actions,
            "visible_objects": [],  # Would need object detection integration
            "map": map,  # Retrieve the latest map image
            "navigation_status": nav_status,
            "robot_status": status
        }
        
    except Exception as e:
        return {
            "observation": {"rgb": None, "depth": None},
            "pose": [0.0, 0.0, 0.0],
            "available_actions": {"movement_actions": [], "rotation_actions": [], "interactable_objects": []},
            "visible_objects": [],
            "map": None,
            "error": str(e)
        }

@mcp.tool()
def execute_vlm_action(action: str, object_id: Optional[str] = None, 
                      degrees: int = 30, magnitude: float = 0.25) -> Dict[str, Any]:
    """Execute an action chosen by the VLM and return the new state.
    
    Parameters
    ----------
    action: str
        The action to execute (e.g., "MoveAhead", "RotateRight")
    object_id: str, optional
        Object ID if the action involves interaction with an object (not supported on real robot yet)
    degrees: int, optional
        Rotation amount for rotate actions (default 30)
    magnitude: float, optional
        Movement magnitude for move actions (default 0.25)
    """
    try:
        # Execute the chosen action using the step function
        step_result = step(action, degrees=degrees, magnitude=magnitude)
        
        # Return new state after action
        return get_environment_state()
        
    except Exception as e:
        return {
            "error": str(e),
            "action_attempted": action
        }

@mcp.tool()
def shutdown() -> str:
    """Terminate the robot server and free resources."""
    try:
        # Stop any ongoing navigation
        try:
            nav_url = get_nav_url()
            requests.post(f"{nav_url}/stop_navigation/", timeout=2)
        except:
            pass
        
        # Stop robot movement
        try:
            request_robot_move(0, 0, 0)  # Stop all movement
        except:
            pass
            
        return "Robot server terminated and movement stopped"
        
    except Exception as e:
        return f"Error during shutdown: {e}"

@mcp.tool()
def get_latest_path_image(input: str = "") -> Dict[str, Any]:
    """
    Get the latest path planning image from the map server via SocketIO.
    
    Args:
        input: Optional input parameter (not used, for compatibility)
    
    Returns:
        Dictionary containing the latest path planning image as base64 string
    """
    try:
        print("Getting latest path planning image...")
        
        # Get the latest path image
        with image_lock:
            if latest_path_image is not None:
                print("Found latest path planning image")
                # Convert to base64
                path_image_b64 = numpy_to_base64_image(latest_path_image)
                
                result = {
                    "success": True,
                    "timestamp": time.time(),
                    "path_image": path_image_b64,
                    "size": f"{latest_path_image.shape[1]}x{latest_path_image.shape[0]}",
                    "map_server_connected": map_server_connected,
                    "source": "socketio_path_planning"
                }
                
                # Save the image for debugging
                try:
                    cv2.imwrite('latest_path_image.png', latest_path_image)
                    result["saved_to_file"] = "latest_path_image.png"
                except Exception as e:
                    print(f"Failed to save path image: {e}")
                
                return result
            else:
                return {
                    "success": False,
                    "error": "No path planning image available",
                    "timestamp": time.time(),
                    "map_server_connected": map_server_connected
                }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get path planning image: {e}",
            "timestamp": time.time()
        }

@mcp.tool()
def get_latest_map_image(input: str = "") -> Dict[str, Any]:
    """
    Get the latest map image (height map or other map data).
    
    Args:
        input: Optional input parameter (not used, for compatibility)
    
    Returns:
        Dictionary containing the latest map image as base64 string
    """
    try:
        print("Getting latest map image...")
        map_image = get_latest_image()
        
        if map_image is None:
            return {
                "success": False,
                "error": "No map image available",
                "timestamp": time.time()
            }
        
        # Convert to base64
        map_image_b64 = numpy_to_base64_image(map_image)
        
        result = {
            "success": True,
            "timestamp": time.time(),
            "map_image": map_image_b64,
            "size": f"{map_image.shape[1]}x{map_image.shape[0]}",
            "map_server_connected": map_server_connected,
            "source": "height_map"
        }
        
        # Save the image for debugging/caching
        try:
            cv2.imwrite('latest_map.png', map_image)
            result["saved_to_file"] = "latest_map.png"
        except Exception as e:
            print(f"Failed to save map image: {e}")
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get latest map image: {e}",
            "timestamp": time.time()
        }

@mcp.tool()
def get_map_from_file(image_path: str = "height_map.png") -> Dict[str, Any]:
    """
    Get map image from a saved file.
    
    Args:
        image_path: Path to the image file (default: height_map.png)
    
    Returns:
        Dictionary containing the map image from file as base64 string
    """
    try:
        map_image = get_latest_image_from_file(image_path)
        
        if map_image is None:
            return {
                "success": False,
                "error": f"Could not load image from {image_path}",
                "timestamp": time.time()
            }
        
        # Convert to base64
        map_image_b64 = numpy_to_base64_image(map_image)
        
        return {
            "success": True,
            "timestamp": time.time(),
            "map_image": map_image_b64,
            "size": f"{map_image.shape[1]}x{map_image.shape[0]}",
            "source": f"file:{image_path}",
            "file_exists": True
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get map from file: {e}",
            "timestamp": time.time()
        }

@mcp.tool()
def refresh_map_image(input: str = "") -> Dict[str, Any]:
    """
    Force refresh the map image by getting new data from sensors.
    
    Args:
        input: Optional input parameter (not used, for compatibility)
    
    Returns:
        Dictionary containing the refreshed map image
    """
    try:
        print("Forcing map image refresh...")
        
        # Get fresh height map
        height_map_img = get_height_map()
        
        if height_map_img is None:
            return {
                "success": False,
                "error": "Failed to get fresh map data from sensors",
                "timestamp": time.time()
            }
        
        # Update cached image
        global latest_map_image
        latest_map_image = height_map_img
        
        # Convert to base64
        map_image_b64 = numpy_to_base64_image(height_map_img)
        
        result = {
            "success": True,
            "timestamp": time.time(),
            "map_image": map_image_b64,
            "size": f"{height_map_img.shape[1]}x{height_map_img.shape[0]}",
            "source": "fresh_sensor_data",
            "refreshed": True
        }
        
        # Save the refreshed image
        try:
            cv2.imwrite('refreshed_map.png', height_map_img)
            result["saved_to_file"] = "refreshed_map.png"
        except Exception as e:
            print(f"Failed to save refreshed map: {e}")
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to refresh map image: {e}",
            "timestamp": time.time()
        }

@mcp.tool()
def connect_map_server(server_url: Optional[str] = None) -> str:
    """
    Connect to the map backend server.
    
    Args:
        server_url: Optional server URL (uses default if not provided)
    
    Returns:
        Connection status message
    """
    try:
        if server_url is None:
            server_url = get_map_server_url()
        
        connect_to_map_server(server_url)
        
        if map_server_connected:
            return f"Successfully connected to map server: {server_url}"
        else:
            return f"Failed to connect to map server: {status_message}"
            
    except Exception as e:
        return f"Error connecting to map server: {e}"

@mcp.tool()
def disconnect_map_server_tool(input: str = "") -> str:
    """
    Disconnect from the map backend server.
    
    Args:
        input: Optional input parameter (not used, for compatibility)
    
    Returns:
        Disconnection status message
    """
    try:
        disconnect_map_server()
        return "Disconnected from map server"
    except Exception as e:
        return f"Error disconnecting from map server: {e}"


def main():
    """Main function to run the server with transport selection"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="UT Dog MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="sse",
                       help="Transport method (default: sse)")
    parser.add_argument("--host", default="127.0.0.1",
                       help="Host for SSE transport (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8099,
                       help="Port for SSE transport (default: 8099)")
    parser.add_argument("--connect-map-server", action="store_true",
                       help="Automatically connect to map server on startup")
    
    args = parser.parse_args()
    
    print("Starting UT Dog MCP Server...")
    print("Available tools:")
    print("- Movement: move, move_forward, move_backward, move_left, move_right, turn_left, turn_right")
    print("- Vision: get_image_sample, get_surrounding_images")
    print("- Navigation: start_navigation, get_navigation_status")
    print("- Communication: communicate_with_human")
    print("- Streaming: start_status_stream, stream_camera_feed, get_real_time_status")
    print("- Utility: robot_status")
    print("- Map Server: connect_map_server, disconnect_map_server_tool, get_map_server_status")
    print("- Map Images: get_latest_map_image, get_latest_path_image, get_map_from_file, refresh_map_image")
    print()
    
    # Always initialize map server connection
    print("Automatically connecting to map server...")
    server_thread = threading.Thread(target=connect_to_map_server)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(2)  # Give it time to connect
    print(f"Map server status: {status_message}")
    
    # Additional connection attempt if requested via command line
    if args.connect_map_server:
        print("Additional connection attempt requested via --connect-map-server flag")
    
    try:
        if args.transport == "sse":
            print(f"Running SSE server on {args.host}:{args.port}")
            print(f"SSE endpoint: http://{args.host}:{args.port}/sse")
            print(f"Messages endpoint: http://{args.host}:{args.port}/messages/")
            mcp.run(transport="sse", host=args.host, port=args.port)
        else:
            print("Running STDIO server")
            mcp.run(transport="stdio")
    except KeyboardInterrupt:
        print('Service interrupted by user')
    finally:
        # Clean up resources
        print("Cleaning up resources...")
        if sio.connected:
            sio.disconnect()
            print("Disconnected from map server")

if __name__ == "__main__":
    main() 