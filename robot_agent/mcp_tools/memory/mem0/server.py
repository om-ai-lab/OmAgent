from __future__ import annotations
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.routing import Mount, Route
from mcp.server import Server
import uvicorn
from mem0 import MemoryClient
from dotenv import load_dotenv
import json
import os

load_dotenv()

# Initialize FastMCP server for mem0 tools
mcp = FastMCP("mem0-mcp")

# Initialize mem0 client and set default user
mem0_client = MemoryClient()
ROBOT_USER_ID = "navigation_robot"

# Custom instructions focused on robot navigation
ROBOT_CUSTOM_INSTRUCTIONS = """
Extract the Following Information:

- Visual Observations: Detailed descriptions of what the robot sees in the environment
- Spatial Information: Locations, landmarks, and navigation points
- Object Details: Descriptions and characteristics of objects encountered
- Environmental Conditions: Lighting, weather, and other environmental factors
- Temporal Information: When observations were made and any time-dependent changes
"""

# Update project with robot-focused instructions
mem0_client.update_project(custom_instructions=ROBOT_CUSTOM_INSTRUCTIONS)

@mcp.tool(
    description="""Store robot observations in mem0. This tool stores detailed descriptions of what the robot
    observes in the real world. When storing observations, include:
    - Visual descriptions of surroundings and objects
    - Spatial information (locations, distances, orientations)
    - Object properties (size, color, shape, function)
    - Environmental conditions (lighting, weather, etc.)
    - Time of observation
    - Any changes observed from previous observations
    The observations will be indexed for semantic search and can be retrieved later."""
)
async def store_robot_observation(observation: str) -> str:
    """Store a robot observation in mem0.

    This tool is designed to capture what the robot observes in the real world.
    
    Args:
        observation: Detailed description of what the robot observes
    """
    try:
        messages = [{"role": "user", "content": observation}]
        mem0_client.add(messages, user_id=ROBOT_USER_ID, output_format="v1.1")
        return f"Successfully stored observation: {observation[:50]}..." if len(observation) > 50 else f"Successfully stored observation: {observation}"
    except Exception as e:
        return f"Error storing observation: {str(e)}"

@mcp.tool(
    description="""Search through stored robot observations. This tool should be called when the robot needs to
    recall previous observations about:
    - Previously observed objects or landmarks
    - Spatial information about the environment
    - Changes observed over time
    - Navigation history
    The search uses natural language understanding to find relevant matches."""
)
async def search_robot_observations(query: str) -> str:
    """
    Search robot observations using semantic search.

    Parameters
    ----------
    query : str
        Search query describing what the robot is looking for.

    Returns
    -------
    str
        A JSON formatted string containing the search results, ranked by relevance.
    """
    try:
        memories = mem0_client.search(query, user_id=ROBOT_USER_ID, output_format="v1.1")
        flattened_memories = [memory["memory"] for memory in memories["results"]]
        return json.dumps(flattened_memories, indent=2)
    except Exception as e:
        return f"Error searching observations: {str(e)}"

@mcp.tool(
    description="""Compare current observation with previous observations to detect changes in the environment.
    This tool is useful for:
    - Identifying objects that have moved
    - Detecting new objects that weren't there before
    - Noticing changes in environmental conditions
    - Tracking dynamic elements in the environment over time
    It helps the robot understand how the environment evolves."""
)
async def detect_environment_changes(current_observation: str, location: str) -> str:
    """
    Compare current observation with previous observations at the same location to detect changes.

    Parameters
    ----------
    current_observation : str
        The current observation to compare against previous ones
    location : str
        The location identifier to search for previous observations

    Returns
    -------
    str
        A description of detected changes or lack thereof
    """
    try:
        # First, store the current observation
        await store_robot_observation(f"{current_observation} Location: {location}")
        
        # Then, query previous observations at this location
        query = f"What did I previously observe at location {location}?"
        previous_memories = json.loads(await search_robot_observations(query))
        
        if not previous_memories:
            return f"No previous observations found at {location}. This is new territory."
        
        # Compare current with previous (simple approach)
        # In a real implementation, this would use more sophisticated comparison
        return json.dumps({
            "current_observation": current_observation,
            "previous_observations": previous_memories[:2],  # Just compare with the top 2
            "location": location
        }, indent=2)
    except Exception as e:
        return f"Error detecting changes: {str(e)}"

# Updated type annotations to Python >3.11 style and added numpy-style docstrings with examples
def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """
    Create a Starlette application that can serve the provided MCP server with SSE.

    Parameters
    ----------
    mcp_server : Server
        The MCP server instance to serve.
    debug : bool, optional
        Whether to enable debug mode, by default False.

    Returns
    -------
    Starlette
        A configured Starlette application.

    Examples
    --------
    >>> from mcp.server import Server
    >>> server = Server()
    >>> app = create_starlette_app(server, debug=True)
    """
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,  # noqa: SLF001
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )


if __name__ == "__main__":
    mcp_server = mcp._mcp_server

    import argparse

    parser = argparse.ArgumentParser(description='Run MCP SSE-based server')
    parser.add_argument('--host', default=os.getenv("HOST", '0.0.0.0'), help='Host to bind to')
    parser.add_argument('--port', type=int, default=int(os.getenv("PORT", 8080)), help='Port to listen on')
    args = parser.parse_args()

    # Bind SSE request handling to MCP server
    starlette_app = create_starlette_app(mcp_server, debug=True)

    # Use the port from CLI arguments
    uvicorn.run(starlette_app, host=args.host, port=args.port)
