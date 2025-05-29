#!/usr/bin/env python3
"""
Robot Server Switcher

A utility script to easily switch between Thor simulator and UT Dog robot servers.
Both servers provide the same unified MCP interface.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Server configurations
SERVERS = {
    "simulator": {
        "name": "AI2-THOR Simulator",
        "script": "simulator/ai2thor/thor_mcp_server.py",
        "description": "AI2-THOR indoor environment simulator with depth sensing and occupancy mapping",
        "features": ["RGB Images", "Depth Images", "Occupancy Maps", "Object Interaction", "Precise Localization"]
    },
    "robot": {
        "name": "Unitree Go2 Robot Dog", 
        "script": "ut_dog_control/ut_dog_server.py",
        "description": "Real Unitree Go2 robot dog with navigation and human communication",
        "features": ["RGB Images", "Real-world Physics", "Navigation Service", "Human Communication", "Safety Constraints"]
    }
}

def print_server_info():
    """Print information about available servers."""
    print("Available Robot Servers:")
    print("=" * 50)
    
    for key, config in SERVERS.items():
        print(f"\n{key.upper()}: {config['name']}")
        print(f"Description: {config['description']}")
        print(f"Features: {', '.join(config['features'])}")
        print(f"Script: {config['script']}")

def generate_mcp_config(server_type: str, output_file: str = None):
    """Generate MCP client configuration for the specified server."""
    if server_type not in SERVERS:
        print(f"Error: Unknown server type '{server_type}'")
        return False
    
    config = SERVERS[server_type]
    script_path = os.path.join(os.path.dirname(__file__), config["script"])
    
    mcp_config = {
        "mcpServers": {
            "robot": {
                "command": "python",
                "args": [script_path],
                "description": config["description"]
            }
        }
    }
    
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(mcp_config, f, indent=2)
        print(f"MCP configuration saved to: {output_file}")
    else:
        print("MCP Configuration:")
        print(json.dumps(mcp_config, indent=2))
    
    return True

def run_server(server_type: str):
    """Run the specified server."""
    if server_type not in SERVERS:
        print(f"Error: Unknown server type '{server_type}'")
        return False
    
    config = SERVERS[server_type]
    script_path = os.path.join(os.path.dirname(__file__), config["script"])
    
    if not os.path.exists(script_path):
        print(f"Error: Server script not found: {script_path}")
        return False
    
    print(f"Starting {config['name']}...")
    print(f"Script: {script_path}")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Run the server script
        subprocess.run([sys.executable, script_path], check=True)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"Error running server: {e}")
        return False
    
    return True

def check_dependencies(server_type: str):
    """Check if dependencies for the specified server are available."""
    print(f"Checking dependencies for {SERVERS[server_type]['name']}...")
    
    if server_type == "simulator":
        try:
            import ai2thor
            import cv2
            import numpy as np
            import matplotlib
            print("✅ All simulator dependencies are available")
            return True
        except ImportError as e:
            print(f"❌ Missing simulator dependency: {e}")
            print("Install with: pip install ai2thor opencv-python numpy matplotlib")
            return False
    
    elif server_type == "robot":
        try:
            import requests
            import websocket
            import cv2
            import numpy as np
            print("✅ All robot dependencies are available")
            return True
        except ImportError as e:
            print(f"❌ Missing robot dependency: {e}")
            print("Install with: pip install requests websocket-client opencv-python numpy")
            return False
    
    return False

def main():
    parser = argparse.ArgumentParser(
        description="Switch between Thor simulator and UT Dog robot servers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python switch_robot.py --info                    # Show server information
  python switch_robot.py --run simulator           # Run Thor simulator
  python switch_robot.py --run robot               # Run UT Dog robot
  python switch_robot.py --config simulator        # Generate MCP config for simulator
  python switch_robot.py --check robot             # Check robot dependencies
        """
    )
    
    parser.add_argument("--info", action="store_true", 
                       help="Show information about available servers")
    parser.add_argument("--run", choices=["simulator", "robot"],
                       help="Run the specified server")
    parser.add_argument("--config", choices=["simulator", "robot"],
                       help="Generate MCP configuration for the specified server")
    parser.add_argument("--config-file", type=str,
                       help="Output file for MCP configuration (default: print to stdout)")
    parser.add_argument("--check", choices=["simulator", "robot"],
                       help="Check dependencies for the specified server")
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    if args.info:
        print_server_info()
    
    if args.check:
        check_dependencies(args.check)
    
    if args.config:
        generate_mcp_config(args.config, args.config_file)
    
    if args.run:
        if not check_dependencies(args.run):
            print("Cannot run server due to missing dependencies")
            return
        run_server(args.run)

if __name__ == "__main__":
    main() 