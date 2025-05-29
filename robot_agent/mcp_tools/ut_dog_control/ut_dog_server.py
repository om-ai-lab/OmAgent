#!/usr/bin/env python3
"""
UT Dog MCP Server - A comprehensive MCP server for Unitree Go2 robot dog control.

This server provides tools for:
- Robot movement (forward, backward, left, right, turn)
- Image capture and surrounding view
- Navigation and status monitoring
- Human communication
"""

import asyncio
import base64
import io
import json
import math
import time
import traceback
from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import cv2
import numpy as np
import requests
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

# Default URLs - can be overridden via environment variables
DEFAULT_ROBOT_URL = "http://172.16.44.211:18080"
DEFAULT_AUDIO_URL = "http://172.16.44.211:8080"
DEFAULT_NAV_URL = "http://localhost:8765"

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

def request_robot_move(vx: float, vy: float, vyaw: float) -> Dict[str, Any]:
    """Send movement command to robot."""
    url = urljoin(get_robot_url(), MOVE_SUFFIX)
    response = requests.post(url, json={"vx": vx, "vy": vy, "vyaw": vyaw}).json()
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
def get_pose() -> List[float]:
    """Return the current robot pose as [x, z, yaw].
    
    Note: For real robot, this returns estimated/placeholder values since
    we don't have precise localization without additional sensors.
    """
    try:
        # For real robot, we would need to integrate with localization system
        # For now, return placeholder values
        # In a real implementation, this would query the robot's odometry or SLAM system
        return [0.0, 0.0, 0.0]  # [x, z, yaw] - placeholder values
    except Exception as e:
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
        
        return {
            "observation": {
                "rgb": observation.get("rgb"),
                "depth": None,  # Real robot doesn't have depth
            },
            "pose": pose,
            "available_actions": available_actions,
            "visible_objects": [],  # Would need object detection integration
            "map": None,  # Real robot doesn't have occupancy mapping
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

if __name__ == "__main__":
    # Run the MCP server
    print("Starting UT Dog MCP Server...")
    print("Available tools:")
    print("- Movement: move, move_forward, move_backward, move_left, move_right, turn_left, turn_right")
    print("- Vision: get_image_sample, get_surrounding_images")
    print("- Navigation: start_navigation, get_navigation_status")
    print("- Communication: communicate_with_human")
    print("- Utility: robot_status")
    print()
    
    mcp.run() 