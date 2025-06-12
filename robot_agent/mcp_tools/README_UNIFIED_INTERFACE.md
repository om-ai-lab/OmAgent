# Unified Robot Interface

This document describes the unified interface between the AI2-THOR simulator (`thor_mcp_server.py`) and the real Unitree Go2 robot dog (`ut_dog_server.py`). Both servers now provide the same MCP tool interface, allowing you to easily switch between simulation and real robot deployment.

## Quick Start

### Running the Thor Simulator
```bash
cd robot_agent/mcp_tools/simulator/ai2thor/
python thor_mcp_server.py
```

### Running the UT Dog Robot
```bash
cd robot_agent/mcp_tools/ut_dog_control/
python ut_dog_server.py
```

## Unified Tool Interface

Both servers provide the following identical MCP tools:

### Core Movement Tools
- `move(vx, vy, vyaw)` - Velocity-based movement control
- `move_forward()` - Move forward
- `move_backward()` - Move backward  
- `move_left()` - Move left
- `move_right()` - Move right
- `turn_left()` - Turn left (counterclockwise)
- `turn_right()` - Turn right (clockwise)

### Low-Level Control Tools
- `step(action, degrees, magnitude, return_map)` - Execute discrete actions
- `get_pose()` - Get current position [x, z, yaw]
- `move_to(x, z)` - Move to specific coordinates

### Vision Tools
- `capture_observation()` - Get RGB (and depth for simulator) images
- `get_image_sample()` - Capture single image
- `get_surrounding_images()` - Capture 360° view (8 images)

### Navigation Tools
- `start_navigation(goal)` - Navigate to target object/location
- `get_navigation_status()` - Get current navigation status
- `execute_navigation_proposal(proposal_index, proposals_text)` - Execute VLM navigation proposals

### Environment State Tools
- `get_environment_state()` - Comprehensive environment state for VLM
- `get_available_actions()` - Get valid actions at current position
- `get_map()` - Get occupancy map (simulator only)

### VLM Integration Tools
- `execute_vlm_action(action, object_id, degrees, magnitude)` - Execute VLM-chosen actions

### Utility Tools
- `reset_environment(environment_id)` - Reset environment/robot state
- `robot_status()` - Get system status
- `communicate_with_human(goal, max_turns)` - Human communication interface
- `shutdown()` - Clean shutdown

## Key Differences Between Simulator and Real Robot

### Thor Simulator Features
- **Occupancy Mapping**: Generates detailed occupancy maps from depth data
- **Depth Images**: Provides depth camera data alongside RGB
- **Object Detection**: Built-in object detection and interaction
- **Precise Localization**: Exact position tracking
- **Teleportation**: Instant movement to coordinates via `move_to()`

### UT Dog Robot Features  
- **Real-World Physics**: Subject to real-world constraints and dynamics
- **Navigation Service**: Uses external navigation system for pathfinding
- **Human Communication**: Can integrate with TTS/ASR systems
- **Safety Constraints**: Movement limited by safety considerations
- **Estimated Localization**: Position estimates (requires integration with SLAM)

### Capability Matrix

| Feature | Thor Simulator | UT Dog Robot |
|---------|---------------|--------------|
| RGB Images | ✅ | ✅ |
| Depth Images | ✅ | ❌ |
| Occupancy Maps | ✅ | ❌ |
| Precise Localization | ✅ | ⚠️ (requires SLAM) |
| Object Interaction | ✅ | ❌ |
| Real-time Navigation | ✅ | ✅ |
| Human Communication | ⚠️ (simulated) | ✅ |
| Safety Constraints | ❌ | ✅ |

## Usage Examples

### Basic Movement (Same for Both)
```python
# Move forward 1 meter
move(vx=1.0, vy=0, vyaw=0)

# Turn right 90 degrees  
move(vx=0, vy=0, vyaw=-1.57)  # -π/2 radians

# Simple movements
move_forward()
turn_left()
```

### Navigation (Same for Both)
```python
# Navigate to a target
start_navigation("laptop")

# Check navigation status
get_navigation_status()
```

### Vision (Same for Both)
```python
# Get current view
observation = capture_observation()
rgb_image = observation["rgb"]  # Base64 encoded image

# Get 360° view
get_surrounding_images()
```

### VLM Integration (Same for Both)
```python
# Get comprehensive state for VLM decision making
state = get_environment_state()

# Execute VLM-chosen action
execute_vlm_action("MoveAhead", degrees=30, magnitude=0.5)
```

## Configuration

### Environment Variables for UT Dog Robot
```bash
export ROBOT_URL="http://172.16.44.211:18080"      # Robot control URL
export AUDIO_URL="http://172.16.44.211:8080"       # Audio service URL  
export NAV_URL="http://localhost:8765"              # Navigation service URL
```

### Environment Variables for Thor Simulator
```bash
# No special configuration needed - uses default AI2-THOR settings
```

## Switching Between Simulator and Robot

To switch from simulator to real robot (or vice versa), simply:

1. **Stop the current server**
2. **Start the other server** 
3. **Update your MCP client configuration** to point to the new server
4. **Use the same tool calls** - the interface is identical!

### Example MCP Client Configuration
```json
{
  "mcpServers": {
    "robot": {
      "command": "python",
      "args": ["robot_agent/mcp_tools/ut_dog_control/ut_dog_server.py"]
    }
  }
}
```

Or for simulator:
```json
{
  "mcpServers": {
    "robot": {
      "command": "python", 
      "args": ["robot_agent/mcp_tools/simulator/ai2thor/thor_mcp_server.py"]
    }
  }
}
```

## Error Handling

Both servers provide consistent error handling:

- **Success**: `{"code": "0", "message": "Success"}`
- **Failure**: `{"code": "1", "message": "Error description"}`
- **Graceful degradation**: Missing features return `None` or appropriate fallback values

## Development Notes

### Adding New Features
When adding new features, ensure they are implemented in both servers:

1. Add the tool function to both `thor_mcp_server.py` and `ut_dog_server.py`
2. Use appropriate fallbacks for missing capabilities
3. Maintain consistent return formats
4. Update this documentation

### Testing
Test your code with both servers to ensure compatibility:

```bash
# Test with simulator
python thor_mcp_server.py

# Test with real robot  
python ut_dog_server.py
```

This unified interface enables seamless development and deployment across simulation and real-world environments! 