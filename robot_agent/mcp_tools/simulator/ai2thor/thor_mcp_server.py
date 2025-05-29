from fastmcp import FastMCP, Image
from typing import Any, Dict, List, Optional, Tuple
import os
import base64
from io import BytesIO
import numpy as np
from PIL import Image as PILImage

import sys
from ai2thor.controller import Controller
import numpy as np
import cv2
import os
import logging
import math

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.collections import LineCollection
from matplotlib.patches import Patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ThorEnv')

class ThorEnvDogView(object):
    def __init__(self, floor_id) -> None:
        if floor_id.startswith("FloorPlan_"): # make the robot as default mode, which supports crouch and lookdown
           self.agentMode = "locobot"  
        else:
           self.agentMode = "default"

        self.controller = Controller(
            agentMode=self.agentMode,
            scene=floor_id,
            width=720,
            height=480,
            fieldOfView=80,

            # step sizes
            gridSize=0.1,
            snapToGrid=True,
            rotateStepDegrees=90,    

            # image modalities
            renderDepthImage=True,
            renderInstanceSegmentation=False
        )
        if self.agentMode == "default": # only default can crouch
            self.controller.step("Crouch")
        self.controller.step("LookDown", degrees=30)


        self.camera_fov = self.controller.initialization_parameters['fieldOfView']
        self.camera_pitch = self.controller.last_event.metadata["agent"]["cameraHorizon"] #30
        self.camera_height = self.controller.last_event.metadata["agent"]["position"]["y"] #0.9
        
        self.logs_dir = "envs/thor_env/logs"
        # Ensure logs directory exists
        os.makedirs(self.logs_dir, exist_ok=True)
        self._init_position()

    def _init_position(self):
        """Initialize position, similar to the crouch and lookdown in ThorEnvDogView"""
        # In the real dog, we might not need this or could use a specific movement

        
        self.scene_bounds = self._get_scene_bounds()
        x_min, x_max = self.scene_bounds["x_range"]
        z_min, z_max = self.scene_bounds["z_range"]
        
        # Calculate map size and resolution
        x_range = x_max - x_min
        z_range = z_max - z_min

        map_shape_x = 200
        map_shape_z = int(map_shape_x * (z_range / x_range))

        self.map_shape = [map_shape_x, map_shape_z]
        self.pixels_per_meter = self.map_shape[0] / x_range


                
        x_size, z_size = self.map_shape
        # Create blank map (-1: unexplored, 0: passable, 1: obstacle, 2: unnavigable)
        self.omap = np.full((x_size, z_size), -1)  # Initialize as unexplored
        self.get_map()
    
    def reset(self, floor_id):
        self.controller.reset(scene=floor_id)
        if self.agentMode == "default": # only default can crouch
            self.controller.step("Crouch")
        self.controller.step("LookDown")

    def _get_scene_bounds(self):
        """Get the position range of the current scene"""
        objects = self.controller.last_event.metadata["objects"]
        
        # Initialize minimum and maximum coordinates
        min_x, min_z = float('inf'), float('inf')
        max_x, max_z = float('-inf'), float('-inf')
        
        # Traverse all objects to find boundaries
        for obj in objects:
            pos = obj["position"]
            min_x = min(min_x, pos["x"])
            max_x = max(max_x, pos["x"])
            min_z = min(min_z, pos["z"])
            max_z = max(max_z, pos["z"])
        
        return {
            "x_range": [min_x, max_x],
            "z_range": [min_z, max_z]
        }

    def _visualize_map(self, map, position):
        """
        Visualize the map and mark the current robot position.
        
        Args:
            map: Occupancy map data
            position: Robot position [x, z, yaw]
        """
        # Create custom color mapping
        colors = ['#DDDDDD', '#8ABE9B', '#333333', '#555555']  # Light gray(unexplored), green(passable), black(obstacle), dark gray(unnavigable)
        cmap = ListedColormap(colors)
        
        # Adjust map values to match color mapping
        occupancy_map = np.array(map)
        display_map = occupancy_map + 1
        
        # Check converted values
        unique_display_values = np.unique(display_map)
        logger.info(f"Values contained in display map: {unique_display_values}")
        
        # Get scene boundaries and map size
        x_min = self.scene_bounds["x_range"][0]
        x_max = self.scene_bounds["x_range"][1]
        z_min = self.scene_bounds["z_range"][0]
        z_max = self.scene_bounds["z_range"][1]
        x_range = x_max - x_min
        z_range = z_max - z_min
        x_size, z_size = self.map_shape[0], self.map_shape[1]
        
        # Calculate conversion factors
        world_to_map_factor_x = x_size / x_range
        world_to_map_factor_z = z_size / z_range
        
        # Create figure and axes
        fig, ax = plt.subplots(figsize=(12, 12))
        
        # Display map - modify here: flip Z axis direction
        im = ax.imshow(display_map, cmap=cmap, origin='lower', interpolation='none',
                       extent=[z_max, z_min, x_min, x_max],  # Here swap z_min and z_max positions
                       vmin=0, vmax=3)  # Force set color mapping range
        
        # Mark robot current position on map
        if position and isinstance(position, (list, tuple)) and len(position) >= 3:
            try:
                robot_x, robot_z = position[0], position[1]
                
                # Directly use world coordinates to draw robot position
                ax.plot(robot_z, robot_x, 'ro', markersize=10, label='Robot Position')
                
                # Draw robot field of view sector (replace original blue arrow)
                yaw_rad = math.radians(position[2])
                
                # Define field of view parameters - reduce sector radius
                map_dimension = min(x_range, z_range)
                fov_radius = map_dimension * 0.05 
                fov_angle = self.camera_fov  # Field of view angle matches camera FOV
                
                # In AI2-THOR, 0° orientation is z-axis positive direction, 90° orientation is x-axis positive direction (right-hand coordinate system)
                # Need to correctly calculate sector orientation
                # Original formula: adjusted_yaw = -yaw_rad + math.pi/2
                # Modified formula:
                adjusted_yaw = yaw_rad  # Directly use original angle
                
                # Calculate sector start and end angles
                start_angle = adjusted_yaw - math.radians(fov_angle/2)
                end_angle = adjusted_yaw + math.radians(fov_angle/2)
                
                # Create sector polygon points
                sector_points = [(robot_z, robot_x)]  # Start from center point
                
                # Add points along arc
                steps = 20  # Number of points for approximate arc
                for i in range(steps + 1):
                    angle = start_angle + (i / steps) * (end_angle - start_angle)
                    # Note: In matplotlib, 0° points to right (Z+), counterclockwise is angle increase direction
                    arc_z = robot_z + fov_radius * math.cos(angle)
                    arc_x = robot_x + fov_radius * math.sin(angle)
                    sector_points.append((arc_z, arc_x))
                
                # Draw filled sector - use semi-transparent orange yellow
                sector = plt.Polygon(sector_points, closed=True, 
                                     facecolor='#FFD700', alpha=0.4,  # Reduce transparency
                                     edgecolor='#FFA500', linewidth=1.5,  # Reduce border width
                                     label='Field of View')
                ax.add_patch(sector)
                
                logger.info(f"Robot position marked on map at world coordinates: ({robot_x:.2f}, {robot_z:.2f})")
            except Exception as e:
                logger.error(f"Error marking robot position on map: {str(e)}")
        
        # Add grid lines and ticks
        ax.grid(color='gray', linestyle='--', linewidth=0.5, alpha=0.7)
        
        # Set axis labels
        ax.set_xlabel('Z Coordinate (m)')
        ax.set_ylabel('X Coordinate (m)')
        
        # Add legend and title
        legend_elements = [
            Patch(facecolor='#DDDDDD', edgecolor='k', label='Unexplored Area (-1)'),
            Patch(facecolor='#8ABE9B', edgecolor='k', label='Free Space (0)'),
            Patch(facecolor='#333333', edgecolor='k', label='Obstacle (1)'),
            Patch(facecolor='#555555', edgecolor='k', label='Unnavigable Area (2)'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='r', markersize=10, label='Robot Position'),
            Patch(facecolor='#FFD700', alpha=0.5, edgecolor='#FFA500', label='Field of View')
        ]
        ax.legend(handles=legend_elements, loc='upper right')
        
        # Add title and other information
        ax.set_title(f'Occupancy Map with Robot Position ({position[0]:.2f}, {position[1]:.2f}, {position[2]:.2f}°)')
        
        # Add color bar
        cbar = fig.colorbar(im, ax=ax, ticks=[0, 1, 2, 3])
        cbar.set_label('Map Categories')
        
        # Save image
        output_file = os.path.join(self.logs_dir, "occupancy_map.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()  # Close chart to free memory
        
        logger.info(f"Map visualization saved to {output_file}")
        
        return
    
    def _update_map(self, occupancy_map, position, depth_np, objects):
        """
        Update the occupancymap with the new position according to the depth information
        """
        # Remove dependency on navigability_mask - we'll use depth information only
        if depth_np is None or depth_np.size == 0:
            logger.info("Depth image is None or empty")
            return occupancy_map
    
        # Get depth image dimensions
        height, width = depth_np.shape[:2]
        
        # Calculate horizontal and vertical FOV
        aspect_ratio = width / height
        h_fov = self.camera_fov  # Horizontal FOV
        v_fov = h_fov / aspect_ratio  # Vertical FOV
        
        # Create a temporary map of cells seen in this observation
        seen_cells = set()
        agent_x, agent_y, orientation = position[0], position[1], position[2]
        cell_size = 1/self.pixels_per_meter
        map_size = self.map_shape
        # Process each pixel in the depth image (subsample for efficiency)
        stride = 1  # Process every Nth pixel (reduced from 8 to capture more detail)
        for y in range(0, height, stride):
            for x in range(0, width, stride):
                depth = depth_np[y, x]
                
                # Skip invalid depth values
                if depth <= 0 or np.isnan(depth) or depth > 10.0:  # Ignore very far readings
                    continue
                
                # Assume areas are navigable by default (no navigability mask)
                is_navigable = True
                
                # Convert to real-world distance in meters
                distance = depth

                
                # Calculate angle offsets from center of view
                angle_h = ((x / width) - 0.5) * h_fov
                angle_v = ((y / height) - 0.5) * v_fov
                
                # Adjust for camera pitch
                adjusted_angle_v = angle_v - self.camera_pitch
                
                # Calculate 3D position relative to camera
                # X is right, Y is up, Z is forward in camera space
                z = distance * math.cos(math.radians(adjusted_angle_v))
                y_offset = distance * math.sin(math.radians(adjusted_angle_v))
                x_offset = z * math.tan(math.radians(angle_h))
                
                # Calculate ground distance (in camera space)
                ground_distance = math.sqrt(z**2 + x_offset**2)

                # Skip points that are too close to the agent
                if ground_distance < 0.1:
                    continue
                # Convert to world space coordinates (in meters)
                # In AI2-THOR, 0° orientation is z-axis positive direction, 90° orientation is x-axis positive direction (right-hand coordinate system)
                world_angle = (orientation + angle_h) % 360
                world_angle_rad = math.radians(world_angle)

                # Correctly calculate world coordinates (note angle calculation)
                # In THOR, 0° orientation is Z+, 90° orientation is X+
                world_x = agent_x + ground_distance * math.sin(world_angle_rad)  # sin corresponds to x axis
                world_z = agent_y + ground_distance * math.cos(world_angle_rad)  # cos corresponds to z axis
                
                # Get scene boundaries for coordinate mapping
                x_min = self.scene_bounds["x_range"][0]
                z_min = self.scene_bounds["z_range"][0]
                x_max = self.scene_bounds["x_range"][1]
                z_max = self.scene_bounds["z_range"][1]

                
                # Use same conversion factors as _visualize_map
                world_to_map_factor_x = self.map_shape[0] / (x_max - x_min)
                world_to_map_factor_z = self.map_shape[1] / (z_max - z_min)
                
                # Convert to grid coordinates (consider offset)
                grid_x = int((z_max - world_z) * world_to_map_factor_z)  # Note here use z_max-world_z for grid_x
                grid_y = int((world_x - x_min) * world_to_map_factor_x)  # Keep x axis direction

                
                # Check if within map bounds
                if 0 <= grid_x < map_size[1] and 0 <= grid_y < map_size[0]:
                    # Add to seen cells
                    seen_cells.add((grid_x, grid_y))
                    
                    # Use depth thresholds to determine if an area is an obstacle
                    # Points with depth < threshold are likely obstacles
                    obstacle_depth_threshold = 3.0  # Adjust based on your needs
                    
                    if distance < obstacle_depth_threshold:
                        # Likely an obstacle
                        occupancy_map[grid_y, grid_x] = 1
                    else:
                        # Likely free space
                        occupancy_map[grid_y, grid_x] = 0

        return occupancy_map
    
    def get_map(self, save_map=True):
        """
        Get the map of the current scene
        
        # First determine the scene boundaries, then create the map based on these boundaries
        """

        
        # Get current position
        xy_yaw = self.get_pose()
        
        # update omap
        self.omap = self._update_map(self.omap, xy_yaw, self.get_depth(), []) #todo: add objects
        # Save and visualize map
        if self.omap is not None and save_map:
            self._visualize_map(self.omap, xy_yaw)
            omap = np.array(self.omap)
            np.save(os.path.join(self.logs_dir, "occupancy_map.npy"), omap)  

        return self.omap, xy_yaw
    
    def get_objects(self):
        object = []
        return [{"bbox_2d": [0,0,0,0], "label": "chair"}, {"bbox_2d": [0,100,200,300], "label": "table"}]
    
    def get_visible_objects(self):
        """
        Get detailed information about all visible objects in the current view.
        
        Returns:
            list: List of dictionaries containing object information
        """
        try:
            # Get all objects from the scene
            all_objects = self.controller.last_event.metadata["objects"]
            
            # Filter for visible objects only
            visible_objects = [obj for obj in all_objects if obj["visible"]]
            
            # Create detailed information for each visible object
            object_infos = []
            for obj in visible_objects:
                # Get 2D bounding box if available
                bbox_2d = None
                if "pixelMask" in obj and obj["pixelMask"]:
                    x_vals = [p[0] for p in obj["pixelMask"]]
                    y_vals = [p[1] for p in obj["pixelMask"]]
                    bbox_2d = [min(x_vals), min(y_vals), max(x_vals), max(y_vals)]
                
                # Add relevant object information
                object_info = {
                    "objectId": obj["objectId"],
                    "name": obj["name"],
                    "distance": obj["distance"],
                    "position": obj["position"],
                    "bbox_2d": bbox_2d,
                    "isPickupable": obj["pickupable"],
                    "isMoveable": obj["moveable"],
                    "isReceptacle": obj["receptacle"],
                    "parentReceptacles": obj.get("parentReceptacles", []),
                    "objectType": obj["objectType"]
                }
                object_infos.append(object_info)
            
            return object_infos
            
        except Exception as e:
            logger.error(f"Error getting visible objects: {str(e)}")
            return {"error": str(e)}
    
    def get_pose(self):
        """
        Get the current agent's position and orientation in the environment
        
        Returns:
            list: List containing [x, y, yaw], where x and z are the agent's horizontal position coordinates, yaw is the orientation angle
        """
        try:
            # Get position and rotation information from controller's last_event
            position = self.controller.last_event.metadata["agent"]["position"]
            rotation = self.controller.last_event.metadata["agent"]["rotation"]
            
            # Extract x and z coordinates, and use y-axis rotation angle as orientation
            x = position["x"]
            z = position["z"]  # Usually in AI2-THOR, the horizontal plane is x-z plane
            yaw = rotation["y"]  # Y-axis rotation angle represents orientation
            
            return [x, z, yaw]
        except Exception as e:
            logger.error(f"Error getting position information: {str(e)}")
            return {"error": str(e)}
    
    def get_available_actions(self):
        """
        Get the list of valid actions at the current position
        
        Returns:
            dict: Dictionary containing valid movement and interaction actions
        """
        try:
            # Get all reachable positions from current location
            reachable_result = self.controller.step(action="GetReachablePositions", gridSize=0.1)
            reachable_positions = reachable_result.metadata["actionReturn"]
            
            # Get current position
            current_pos = self.controller.last_event.metadata["agent"]["position"]
            
            # Check which movement actions are valid
            valid_movements = []
            directions = {
                "MoveAhead": (0, 1), 
                "MoveBack": (0, -1),
                "MoveRight": (1, 0),
                "MoveLeft": (-1, 0)
            }
            
            # Get current rotation
            rotation = self.controller.last_event.metadata["agent"]["rotation"]["y"]
            rad_rotation = math.radians(rotation)
            
            for action, (dx, dz) in directions.items():
                # Adjust direction based on current rotation
                rotated_dx = dx * math.cos(rad_rotation) - dz * math.sin(rad_rotation)
                rotated_dz = dx * math.sin(rad_rotation) + dz * math.cos(rad_rotation)
                
                # Scale by movement magnitude
                magnitude = 0.25  # Same as default in step method
                target_x = current_pos["x"] + rotated_dx * magnitude
                target_z = current_pos["z"] + rotated_dz * magnitude
                
                # Check if target position is reachable
                is_reachable = False
                for pos in reachable_positions:
                    dist = ((pos["x"] - target_x) ** 2 + (pos["z"] - target_z) ** 2) ** 0.5
                    if dist < 0.1:  # Within reasonable distance tolerance
                        is_reachable = True
                        break
                
                if is_reachable:
                    valid_movements.append(action)
            
            # Rotation actions are always available
            rotation_actions = ["RotateLeft", "RotateRight"]
            
            # Get interactable objects in view
            visible_objects = [obj for obj in self.controller.last_event.metadata["objects"] 
                              if obj["visible"] and obj["pickupable"]]
            
            interactable_objects = []
            for obj in visible_objects:
                interactable_objects.append({
                    "objectId": obj["objectId"],
                    "name": obj["name"],
                    "distance": obj["distance"]
                })
            
            return {
                "movement_actions": valid_movements,
                "rotation_actions": rotation_actions,
                "interactable_objects": interactable_objects
            }
        except Exception as e:
            logger.error(f"Error getting available actions: {str(e)}")
            return {"error": str(e)}
    
    def step(self, action, degrees=30, magnitude=0.25, return_map=False):
        try:
            if 'Rotate' in action:
                event = self.controller.step(action=action, degrees=degrees)
            elif 'Move' in action:
                event = self.controller.step(action=action, moveMagnitude=magnitude)
            else:
                event = self.controller.step(action=action)
            result = {'code': '0', 'message': ''}
        except Exception as e:
            result = {'code': '1', 'message': str(e)}

        if return_map:
            map, position = self.get_map()
        else:
            map = None
            position = self.get_pose()
        _ = self.get_map(save_map=False)

        return result, map, position


            


        
        return event
    
    def _depth_to_heatmap(self, depth):
        """Convert depth array to heatmap visualization"""
        depth_normalized = cv2.normalize(depth, None, 0, 255, cv2.NORM_MINMAX)
        depth_uint8 = depth_normalized.astype(np.uint8)
        return cv2.applyColorMap(depth_uint8, cv2.COLORMAP_JET)

    def get_observation(self):
        frame = self.controller.last_event.cv2img
        cv2.imwrite(os.path.join(self.logs_dir, "RGB.png"), frame)
        return frame
    
    def get_depth(self):
        depth = self.controller.last_event.depth_frame
        heatmap = self._depth_to_heatmap(depth)
        cv2.imwrite(os.path.join(self.logs_dir, "depth.png"), heatmap)
        return depth
    
    def get_rgb_depth(self):

        return self.get_observation(), self.get_depth()

    def get_asr(self, text):
        """
        Get ASR (Automatic Speech Recognition) response.
        
        In simulation environment, this simply returns the input text
        as if it was recognized from speech.
        
        Input:
            text (str): Text to be processed as if it was spoken
            
        Output:
            str: The same text that was input
        """
        return text

    def send_tts(self, text):
        """
        Get TTS (Text-to-Speech) response.
        
        In simulation environment, this would convert text to speech.
        For now, it simply returns the text.
        
        Input:
            text (str): Text to be converted to speech
            
        Output:
            str: The same text that was input
        """
        return text

    def map_move(self, target_position):
        """
        Move the agent to a target position on the map
        
        Args:
            target_position: [x, z] coordinates in world space
        
        Returns:
            dict: Status information including success/failure and message
        """
        try:
            
            # Check if target position is in valid format
            if not isinstance(target_position, list) or len(target_position) != 2:
                return {"code": 0,
                        "data": {
                            "enabled": False,
                            "status_code": 0,
                            "status_name": "Navigation not started/paused"
                        },
                        "message": "Invalid target format, please input [x, z] coordinates"
                        }
            
            
            # Extract x and z coordinates of target position
            target_x, target_z = target_position[0], target_position[1]
            
            
            # Check if target position is within reachable range
            reachable_check = self.controller.step(
                action="GetReachablePositions",
                gridSize=0.1  # Use same gridSize as controller initialization
            )
            
            reachable_positions = reachable_check.metadata["actionReturn"]
            
            # Check if target position is reachable (find closest reachable point)
            min_distance = float('inf')
            closest_point = None
            
            for pos in reachable_positions:
                dist = ((pos["x"] - target_x) ** 2 + (pos["z"] - target_z) ** 2) ** 0.5
                if dist < min_distance:
                    min_distance = dist
                    closest_point = pos
            # If no sufficiently close point is found
            if closest_point is None:
                return {"code": 0,
                        "data": {
                            "enabled": False,
                            "status_code": 3,
                            "status_name": "Destination unreachable"
                        },
                        "message": "No nearby reachable point found"
                        }
            
            # If closest point is too far from target position (over 0.5 meters), consider target unreachable
            if min_distance > 0.5:
                return {"code": 0,
                        "data": {
                            "enabled": False,
                            "status_code": 3,
                            "status_name": "Destination unreachable"
                        },
                        "message": f"No nearby reachable point found within 0.5m range, closest point distance to target is {min_distance:.2f}m"
                        }
            
            # Attempt to move to closest reachable point
            teleport_result = self.controller.step(
                action="Teleport",
                position=dict(
                    x=round(closest_point["x"], 2),  
                    y=round(closest_point["y"], 2), 
                    z=round(closest_point["z"], 2)   
                )
            )
            
            # Check if movement was successful
            if teleport_result.metadata["lastActionSuccess"]:
                new_position = self.get_pose()
                _ = self.get_map(save_map=False)
                return {"code": 0,
                        "data": {
                            "enabled": False,
                            "status_code": 2,
                            "status_name": "Destination reached"
                        },
                        "message": "Destination reached"
                        }
            else:
                return {"code": 0,
                        "data": {
                            "enabled": False,
                            "status_code": 0,
                            "status_name": "Navigation not started/paused"
                        },
                        "message": teleport_result.metadata.get('errorMessage', 'unknown')
                        }
            
        
        except Exception as e:
            logger.error(f"Error during map movement: {str(e)}")
            return {"code": 0,
                    "data": {
                        "enabled": False,
                        "status_code": 0,
                        "status_name": "Navigation not started/paused"
                    },
                    "message": str(e)
                    }
    
    def execute_navigation_proposal(self, proposal_index, proposals_text):
        """
        Execute a navigation action proposal with specific distance and angle.
        
        Args:
            proposal_index: The index of the proposal to execute (1-based)
            proposals_text: Text containing the navigation action proposals
            
        Returns:
            dict: Result of the action execution
        """
        try:
            # Parse the proposals text to extract the chosen proposal
            proposals = self._parse_navigation_proposals(proposals_text)
            
            if not proposals or proposal_index < 1 or proposal_index > len(proposals):
                return {
                    "success": False,
                    "message": f"Invalid proposal index {proposal_index}. Available proposals: {len(proposals)}"
                }
            
            # Get the selected proposal
            selected_proposal = proposals[proposal_index - 1]  # Convert to 0-based index
            distance = selected_proposal["distance"]
            angle = selected_proposal["angle"]
            
            logger.info(f"Executing navigation proposal {proposal_index}: distance={distance}m, angle={angle}°")
            
            # First rotate to the target angle
            result = self._rotate_to_angle(angle)
            if not result["success"]:
                return result
                
            # Then move the specified distance
            return self._move_distance(distance)
            
        except Exception as e:
            logger.error(f"Error executing navigation proposal: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    def _parse_navigation_proposals(self, proposals_text):
        """
        Parse navigation proposals text into structured data.
        
        Args:
            proposals_text: Text containing navigation action proposals
            
        Returns:
            list: List of dictionaries with proposal details
        """
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
                logger.warning(f"Error parsing proposal line '{line}': {str(e)}")
                
        return proposals
    
    def _rotate_to_angle(self, target_angle):
        """
        Rotate the agent to face the specified angle.
        
        Args:
            target_angle: The target angle in degrees
            
        Returns:
            dict: Result of the rotation
        """
        # Get current rotation
        current_rotation = self.controller.last_event.metadata["agent"]["rotation"]["y"]
        
        # Calculate the angle to rotate (positive = right, negative = left)
        angle_diff = target_angle
        
        # Determine rotation direction and amount
        rotation_step = 30  # Thor's default rotation step
        
        # Calculate number of rotation steps needed
        abs_angle = abs(angle_diff)
        steps_needed = int(abs_angle / rotation_step)
        if abs_angle % rotation_step > 0:
            steps_needed += 1
            
        # Execute the rotation steps
        action = "RotateRight" if angle_diff > 0 else "RotateLeft"
        
        success = True
        for _ in range(steps_needed):
            result, _, _ = self.step(action, degrees=min(rotation_step, abs(angle_diff)))
            if result["code"] != "0":
                success = False
                break
                
            # Update remaining angle
            angle_diff = angle_diff - rotation_step if angle_diff > 0 else angle_diff + rotation_step
            
        return {
            "success": success,
            "message": "Rotation complete" if success else "Rotation failed"
        }
    
    def _move_distance(self, distance):
        """
        Move the agent forward by the specified distance.
        
        Args:
            distance: Distance to move in meters
            
        Returns:
            dict: Result of the movement
        """
        # Calculate number of movement steps (Thor's default step is 0.25m)
        move_step = 0.25
        steps_needed = int(distance / move_step)
        
        # Execute the movement steps
        success = True
        for _ in range(steps_needed):
            result, _, _ = self.step("MoveAhead")
            if result["code"] != "0":
                success = False
                break
                
        return {
            "success": success,
            "message": f"Moved forward {steps_needed * move_step}m" if success else "Movement failed"
        }
    
    def terminate(self):
        return


# Create the FastMCP server instance
mcp = FastMCP("Thor Simulator 🚀", dependencies=["ai2thor", "opencv-python", "numpy", "matplotlib", "pillow"])

# -------------------------------
# Internal state management
# -------------------------------

_env: Optional[ThorEnvDogView] = None  # The underlying simulator instance


def _ensure_env(floor_id: str = "FloorPlan10") -> ThorEnvDogView:
    """Create the simulator if it does not exist."""
    global _env
    if _env is None:
        _env = ThorEnvDogView(floor_id)
    return _env


# -------------------------------
# Helper functions
# -------------------------------

def _image_to_base64(img_path: str) -> str:
    """Read an image from disk and return a base64-encoded data-URL."""
    if not os.path.exists(img_path):
        raise FileNotFoundError(img_path)
    with open(img_path, "rb") as f:
        img_bytes = f.read()
    encoded = base64.b64encode(img_bytes).decode("utf-8")
    ext = os.path.splitext(img_path)[1].lstrip(".").lower()
    mime = "image/png" if ext == "png" else f"image/{ext}"
    return f"data:{mime};base64,{encoded}"


# -------------------------------
# MCP TOOLS
# -------------------------------


@mcp.tool()
def reset_environment(floor_id: str = "FloorPlan10") -> str:
    """Reset the AI2-THOR simulator to a given *floor_id* (e.g. "FloorPlan10").
    
    Parameters
    ----------
    floor_id: str, optional
        The floor plan ID to load (default: "FloorPlan10")
    """
    global _env
    # Dispose of existing env to free resources
    if _env is not None:
        try:
            _env.terminate()
        except Exception:
            pass
        _env = None
    
    # Set up the environment
    _env = ThorEnvDogView(floor_id)
    
    return f"Environment reset to {floor_id}"


@mcp.tool()
def step(action: str, degrees: int = 30, magnitude: float = 0.25, return_map: bool = False) -> Dict[str, Any]:
    """Execute *action* in the simulator.

    Parameters
    ----------
    action: str
        One of AI2-THOR actions such as "MoveAhead", "MoveLeft", "RotateRight", etc.
    degrees: int, optional
        Rotation amount for rotate actions (default 30).
    magnitude: float, optional
        Movement magnitude for move actions (default 0.25).
    return_map: bool, optional
        If *True* include occupancy map in the response.
    """
    env = _ensure_env()
    result, omap, position = env.step(action, degrees=degrees, magnitude=magnitude, return_map=return_map)

    response: Dict[str, Any] = {
        "result": result,
        "position": position,
    }

    if return_map and omap is not None:
        # Convert numpy map to nested python lists for JSON serialisation
        response["map"] = np.asarray(omap).tolist()
    return response


@mcp.tool()
def get_pose() -> List[float]:
    """Return the current agent pose as [x, z, yaw]."""
    env = _ensure_env()
    return env.get_pose()


@mcp.tool()
def move_to(x: float, z: float) -> Dict[str, Any]:
    """Teleport/move the agent to (*x*, *z*) world coordinates using *map_move* helper."""
    env = _ensure_env()
    return env.map_move([x, z])


@mcp.tool()
def execute_navigation_proposal(proposal_index: int, proposals_text: str) -> Dict[str, Any]:
    """Execute a specific navigation action proposal from the given text.
    
    Parameters
    ----------
    proposal_index: int
        The 1-based index of the proposal to execute (e.g., 1 for "Action 1")
    proposals_text: str
        The text containing navigation action proposals (e.g., from vision model output)
        
    Example proposal text format:
    ```
    Navigation Action Proposals:
    Action 1: Distance 1.75m, Angle -30.0° (-0.52 radians), Minimum Width 25.8px
    Action 2: Distance 1.42m, Angle -10.5° (-0.18 radians), Minimum Width 32.1px
    ```
    """
    env = _ensure_env()
    result = env.execute_navigation_proposal(proposal_index, proposals_text)
    
    # Get the updated state after executing the proposal
    if result.get("success", False):
        # Get current position after the move
        position = env.get_pose()
        return {
            "result": result,
            "position": position
        }
    else:
        return {
            "result": result
        }


@mcp.tool()
def capture_observation() -> Dict[str, str]:
    """Capture an RGB frame and depth image and return them as base64 data-URLs."""
    env = _ensure_env()
    rgb, depth = env.get_rgb_depth()

    # Save temporary files in logs directory (already used by env)
    logs_dir = os.path.join(env.logs_dir)
    os.makedirs(logs_dir, exist_ok=True)
    rgb_path = os.path.join(logs_dir, "obs_rgb.png")
    depth_path = os.path.join(logs_dir, "obs_depth.png")

    # Save RGB
    PILImage.fromarray(rgb).save(rgb_path)
    # Convert depth map to a heatmap for visualisation
    max_depth = np.nanmax(depth)
    depth_norm = (depth / max_depth * 255).astype(np.uint8)
    PILImage.fromarray(depth_norm).save(depth_path)

    return {
        "rgb": _image_to_base64(rgb_path),
        "depth": _image_to_base64(depth_path),
    }


@mcp.tool()
def get_map() -> Dict[str, str]:
    """Return the latest occupancy map as a base64 PNG data-URL along with agent pose."""
    env = _ensure_env()
    omap, pose = env.get_map()

    # The env already saves a visualisation to logs/occupancy_map.png
    map_path = os.path.join(env.logs_dir, "occupancy_map.png")
    return {
        "pose": pose,
        "map": _image_to_base64(map_path),
    }


@mcp.tool()
def get_available_actions() -> Dict[str, Any]:
    """Return all valid actions at the current position for the VLM to choose from."""
    env = _ensure_env()
    return env.get_available_actions()


@mcp.tool()
def get_environment_state() -> Dict[str, Any]:
    """Return a comprehensive state of the environment for VLM decision-making.
    
    This includes:
    - Current observation (RGB and depth images)
    - Agent's position and orientation
    - Available actions
    - Map information
    - Visible objects
    """
    env = _ensure_env()
    
    # Get observation images
    rgb, depth = env.get_rgb_depth()
    
    # Save temporary files in logs directory
    logs_dir = os.path.join(env.logs_dir)
    os.makedirs(logs_dir, exist_ok=True)
    rgb_path = os.path.join(logs_dir, "obs_rgb.png")
    depth_path = os.path.join(logs_dir, "obs_depth.png")
    
    # Save RGB and depth images
    PILImage.fromarray(rgb).save(rgb_path)
    max_depth = np.nanmax(depth)
    depth_norm = (depth / max_depth * 255).astype(np.uint8)
    PILImage.fromarray(depth_norm).save(depth_path)
    
    # Get map
    omap, pose = env.get_map()
    map_path = os.path.join(env.logs_dir, "occupancy_map.png")
    
    # Get available actions
    available_actions = env.get_available_actions()
    
    # Get visible objects
    visible_objects = env.get_visible_objects()
    print ("hello")
    # Return comprehensive state
    return {
        "observation": {
            "rgb": _image_to_base64(rgb_path),
            "depth": _image_to_base64(depth_path),
        },
        "pose": pose,
        "available_actions": available_actions,
        "visible_objects": visible_objects,
        "map": _image_to_base64(map_path),
    }


@mcp.tool()
def execute_vlm_action(action: str, object_id: Optional[str] = None, 
                      degrees: int = 30, magnitude: float = 0.25) -> Dict[str, Any]:
    """Execute an action chosen by the VLM and return the new state.
    
    Parameters
    ----------
    action: str
        The action to execute (e.g., "MoveAhead", "RotateRight", "PickupObject")
    object_id: str, optional
        Object ID if the action involves interaction with an object
    degrees: int, optional
        Rotation amount for rotate actions (default 30)
    magnitude: float, optional
        Movement magnitude for move actions (default 0.25)
    """
    env = _ensure_env()
    
    # Execute the chosen action
    if action == "PickupObject" and object_id:
        result, _, position = env.step(f"PickupObject,{object_id}")
    else:
        result, _, position = env.step(action, degrees=degrees, magnitude=magnitude)
    
    # Return new state after action
    return get_environment_state()


@mcp.tool()
def shutdown() -> str:
    """Terminate the simulator and free resources."""
    global _env
    if _env is not None:
        try:
            _env.terminate()
        except Exception:
            pass
        _env = None
    return "Simulator terminated"


# ========================================
# UNIFIED INTERFACE TOOLS (matching UT Dog robot)
# ========================================

@mcp.tool()
def move(vx: float = 0, vy: float = 0, vyaw: float = 0) -> str:
    """
    Control the agent movement using velocity commands.
    
    Args:
        vx: Speed along x-axis (m/s). Positive=forward, negative=backward.
        vy: Speed along y-axis (m/s). Positive=left, negative=right.
        vyaw: Angular velocity (rad/s). Positive=counterclockwise, negative=clockwise.
    
    Returns:
        Movement result message
    """
    try:
        env = _ensure_env()
        
        # Convert velocity commands to discrete Thor actions
        result_parts = ["Successfully moved the agent"]
        
        # Handle forward/backward movement
        if vx > 0:
            # Move forward - calculate number of steps based on velocity
            steps = max(1, int(vx / 0.25))  # Thor's default step is 0.25m
            for _ in range(steps):
                step_result, _, _ = env.step("MoveAhead")
                if step_result["code"] != "0":
                    break
            result_parts.append(f"forward: {vx}m")
        elif vx < 0:
            # Move backward
            steps = max(1, int(abs(vx) / 0.25))
            for _ in range(steps):
                step_result, _, _ = env.step("MoveBack")
                if step_result["code"] != "0":
                    break
            result_parts.append(f"backward: {abs(vx)}m")
        
        # Handle left/right movement
        if vy > 0:
            # Move left
            steps = max(1, int(vy / 0.25))
            for _ in range(steps):
                step_result, _, _ = env.step("MoveLeft")
                if step_result["code"] != "0":
                    break
            result_parts.append(f"left: {vy}m")
        elif vy < 0:
            # Move right
            steps = max(1, int(abs(vy) / 0.25))
            for _ in range(steps):
                step_result, _, _ = env.step("MoveRight")
                if step_result["code"] != "0":
                    break
            result_parts.append(f"right: {abs(vy)}m")
        
        # Handle rotation
        if vyaw != 0:
            # Convert radians to degrees
            degrees = abs(math.degrees(vyaw))
            action = "RotateLeft" if vyaw > 0 else "RotateRight"
            
            # Calculate number of rotation steps (Thor default is 30 degrees)
            steps = max(1, int(degrees / 30))
            for _ in range(steps):
                step_result, _, _ = env.step(action, degrees=min(30, degrees))
                if step_result["code"] != "0":
                    break
                degrees -= 30
                if degrees <= 0:
                    break
            result_parts.append(f"rotate: {vyaw}rad")
        
        return ". ".join(result_parts)
        
    except Exception as e:
        return f"Failed to move the agent: {e}"

@mcp.tool()
def move_forward() -> str:
    """Move the agent forward."""
    return move(vx=0.5, vy=0, vyaw=0)

@mcp.tool()
def move_backward() -> str:
    """Move the agent backward."""
    return move(vx=-0.5, vy=0, vyaw=0)

@mcp.tool()
def move_left() -> str:
    """Move the agent left."""
    return move(vx=0, vy=0.5, vyaw=0)

@mcp.tool()
def move_right() -> str:
    """Move the agent right."""
    return move(vx=0, vy=-0.5, vyaw=0)

@mcp.tool()
def turn_left() -> str:
    """Turn the agent left (counterclockwise)."""
    return move(vx=0, vy=0, vyaw=1.5)

@mcp.tool()
def turn_right() -> str:
    """Turn the agent right (clockwise)."""
    return move(vx=0, vy=0, vyaw=-1.5)

@mcp.tool()
def get_image_sample() -> str:
    """
    Get the current view image from the agent's camera.
    
    Returns:
        Success message with image capture result
    """
    try:
        env = _ensure_env()
        rgb, depth = env.get_rgb_depth()
        
        # Save the image (already done by get_rgb_depth)
        return "Successfully captured front image from agent camera"
        
    except Exception as e:
        return f"Failed to get front image: {e}"

@mcp.tool()
def get_surrounding_images() -> str:
    """
    Get surrounding images by rotating the agent and capturing 8 directional views.
    This takes time, so use only when complete environmental view is necessary.
    
    Returns:
        Success message with surrounding image capture result
    """
    try:
        env = _ensure_env()
        images_captured = 0
        
        for i in range(8):
            # Capture image at current angle
            rgb, depth = env.get_rgb_depth()
            images_captured += 1
            
            # Rotate for next image (except on last iteration)
            if i < 7:
                step_result, _, _ = env.step("RotateRight", degrees=45)  # 360/8 = 45 degrees
                if step_result["code"] != "0":
                    break
        
        return f"Successfully captured surrounding images in 8 directions ({images_captured} images total)"
        
    except Exception as e:
        return f"Failed to get surrounding images: {e}"

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
        env = _ensure_env()
        
        # For simulator, we can search for objects by name
        visible_objects = env.get_visible_objects()
        
        # Look for the goal object in visible objects
        target_object = None
        for obj in visible_objects:
            if goal.lower() in obj["name"].lower() or goal.lower() in obj["objectType"].lower():
                target_object = obj
                break
        
        if target_object:
            # Object is visible, try to move closer
            if target_object["distance"] > 1.5:  # If object is far, move closer
                # Simple approach: move forward a few steps
                for _ in range(3):
                    step_result, _, _ = env.step("MoveAhead")
                    if step_result["code"] != "0":
                        break
                return f"Navigation completed successfully. Target '{goal}' is nearby."
            else:
                return f"Navigation completed successfully. Target '{goal}' is already nearby."
        else:
            # Object not visible, try rotating to find it
            for _ in range(4):  # Try 4 rotations (360 degrees total)
                step_result, _, _ = env.step("RotateRight", degrees=90)
                if step_result["code"] != "0":
                    break
                
                # Check if object is now visible
                visible_objects = env.get_visible_objects()
                for obj in visible_objects:
                    if goal.lower() in obj["name"].lower() or goal.lower() in obj["objectType"].lower():
                        return f"Navigation completed successfully. Target '{goal}' found and is nearby."
            
            return f"Navigation failed. Target '{goal}' is not reachable or not found in the environment."
            
    except Exception as e:
        return f"Failed to start navigation: {e}"

@mcp.tool()
def get_navigation_status() -> str:
    """
    Get the current navigation status of the agent.
    
    Returns:
        Current navigation status description
    """
    try:
        # For simulator, navigation is immediate, so we just return current status
        env = _ensure_env()
        pose = env.get_pose()
        
        return f"Navigation status: Ready. Current position: ({pose[0]:.2f}, {pose[1]:.2f}, {pose[2]:.2f}°)"
        
    except Exception as e:
        return f"Failed to get navigation status: {e}"

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
        # In simulator, this is a placeholder for human communication
        return f"Communication initiated with goal: '{goal}'. In simulation mode, this would connect to a human interface for assistance."
        
    except Exception as e:
        return f"Failed to communicate with human: {e}"

@mcp.tool()
def robot_status() -> str:
    """
    Get overall agent status including connectivity and basic health check.
    
    Returns:
        Agent status summary
    """
    try:
        env = _ensure_env()
        pose = env.get_pose()
        
        # Check if environment is responsive
        try:
            available_actions = env.get_available_actions()
            env_status = "Connected"
        except:
            env_status = "Disconnected"
        
        return f"Agent Status: {env_status}, Position: ({pose[0]:.2f}, {pose[1]:.2f}, {pose[2]:.2f}°), Navigation Service: Available"
        
    except Exception as e:
        return f"Agent Status: Error - {e}"


# -------------------------------
# Entry-point when executed directly
# -------------------------------

if __name__ == "__main__":
    # Default to stdio transport so it can be used with `fastmcp run`.
    mcp.run(host="0.0.0.0", port=3001,transport="sse") 
