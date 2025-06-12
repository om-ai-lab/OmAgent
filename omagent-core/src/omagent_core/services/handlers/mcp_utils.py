import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from omagent_core.services.handlers.mcp_client import MCPClient, TransportType

import logging


def get_config_path() -> Path:
    """Get the path to the MCP config file."""
    # Try to find config in various locations
    possible_paths = [
        Path(__file__).parents[3] / "tool_system" / "mcp.json",  # From tool_system directory
        Path(__file__).parents[4] / "configs" / "mcp.json",      # From source
        Path.home() / ".config" / "omagent" / "mcp.json",       # User config
        Path("/etc/omagent/configs/mcp.json"),                  # System-wide config
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    # If no config file found, return the default path
    return possible_paths[0]  # Default to the tool_system config path

def load_mcp_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load MCP configuration from a JSON file with the new format."""
    if config_path is None:
        config_path = get_config_path()
    
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        logging.info(f"Loaded MCP config from {config_path}")
        return config
    except FileNotFoundError:
        logging.warning(f"MCP config file not found at {config_path}, using defaults")
        return {"mcpServers": {}}
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON in MCP config file at {config_path}, using defaults")
        return {"mcpServers": {}}

def create_mcp_client(config_path: Optional[Path] = None, server_name: Optional[str] = None) -> Optional[MCPClient]:
    """
    Create an MCPClient from config with the new format.
    
    Args:
        config_path: Path to the config file. If None, will search in standard locations.
        server_name: Name of the server to use from the config. If None, will use the first one.
        
    Returns:
        An MCPClient instance or None if no valid servers were found.
    """
    config = load_mcp_config(config_path)
    
    if "mcpServers" not in config or not config["mcpServers"]:
        logging.warning("No MCP servers defined in config.")
        return None
    
    # If server_name is provided, try to use that specific server
    if server_name and server_name in config["mcpServers"]:
        server_config = config["mcpServers"][server_name]
        logging.info(f"Using MCP server '{server_name}' from config")
    else:
        # Otherwise use the first server in the config
        server_name = next(iter(config["mcpServers"].keys()))
        server_config = config["mcpServers"][server_name]
        logging.info(f"No server name provided, using first server '{server_name}' from config")
    
    # Determine transport type from server config
    transport_type = server_config.get("transport", TransportType.STDIO)
    
    if transport_type == TransportType.STDIO:
        # Create a dictionary with command, args, and env for FastMCP
        server_params = {
            "command": server_config.get("command", ""),
            "args": server_config.get("args", []),
            "env": server_config.get("env", {})
        }
        return MCPClient(server_params, transport_type=TransportType.STDIO)
    elif transport_type == TransportType.SSE:
        # For SSE, we need a URL and optional headers
        if "url" not in server_config:
            logging.error(f"SSE transport requires a 'url' field in server config for '{server_name}'")
            return None
        
        # Create a dict with SSE parameters
        sse_params = {
            "url": server_config["url"],
            "headers": server_config.get("headers", {}),
            "timeout": server_config.get("timeout", 30)
        }
        return MCPClient(sse_params, transport_type=TransportType.SSE)
    else:
        logging.error(f"Unsupported transport type '{transport_type}' for server '{server_name}'")
        return None


def create_all_mcp_clients(config_path: Optional[Path] = None) -> Dict[str, MCPClient]:
    """
    Create MCPClient instances for all servers defined in the config.
    
    Args:
        config_path: Path to the config file
        
    Returns:
        Dict mapping server names to MCPClient instances
    """
    config = load_mcp_config(config_path)
    clients = {}
    
    if "mcpServers" not in config:
        return clients
    
    for server_name, server_config in config["mcpServers"].items():
        # Determine transport type
        transport_type = server_config.get("transport", TransportType.STDIO)
        
        if transport_type == TransportType.STDIO:
            # Create a dictionary with command, args, and env for FastMCP
            server_params = {
                "command": server_config.get("command", ""),
                "args": server_config.get("args", []),
                "env": server_config.get("env", {})
            }
            clients[server_name] = MCPClient(server_params, transport_type=TransportType.STDIO)
        elif transport_type == TransportType.SSE:
            # For SSE, verify we have a URL
            if "url" not in server_config:
                logging.error(f"SSE transport requires a 'url' field in server config for '{server_name}'")
                continue
                
            # Create SSE parameters
            sse_params = {
                "url": server_config["url"],
                "headers": server_config.get("headers", {}),
                "timeout": server_config.get("timeout", 30)
            }
            clients[server_name] = MCPClient(sse_params, transport_type=TransportType.SSE)
        else:
            logging.error(f"Unsupported transport type '{transport_type}' for server '{server_name}'")

    
    return clients 