import asyncio
import json
from typing import Any, Dict, List, Optional, Union
from contextlib import AsyncExitStack
import aiohttp

from dotenv import load_dotenv
from fastmcp import Client

load_dotenv()

class TransportType:
    STDIO = "stdio"
    SSE = "sse"


class MCPClient:
    """
    A client class for interacting with the MCP (Model Control Protocol) server.
    This class manages the connection and communication through MCP.
    Supports both stdio and SSE transport types.
    """

    def __init__(self, server_params: Union[Dict[str, Any], str], transport_type: str = TransportType.STDIO):
        """
        Initialize the MCP client with server parameters and transport type
        
        Args:
            server_params: For stdio, a path to the server script or dict with command/args.
                         For SSE, a URL string or dict with 'url' key
            transport_type: One of 'stdio' or 'sse'
        """
        self.server_params = server_params
        self.transport_type = transport_type
        self._client = None
        
        # Configure the client based on transport type
        if self.transport_type == TransportType.STDIO:
            if isinstance(server_params, dict) and "command" in server_params and "args" in server_params:
                # Create a config dict for FastMCP
                self._client = Client({
                    "mcpServers": {
                        "default": {
                            "command": server_params["command"],
                            "args": server_params["args"],
                            "env": server_params.get("env", {})
                        }
                    }
                })
            elif isinstance(server_params, str):
                # Assume it's a script path
                self._client = Client(server_params)
            else:
                raise ValueError("Invalid server parameters for STDIO transport")
                
        elif self.transport_type == TransportType.SSE:
            if isinstance(server_params, dict) and "url" in server_params:
                url = server_params["url"]
                # FastMCP will handle the headers and timeout in the context manager
                self._client = Client(url)
            elif isinstance(server_params, str):
                # Assume it's a URL
                self._client = Client(server_params)
            else:
                raise ValueError("SSE transport requires a URL string or a dict with 'url' key")
        else:
            raise ValueError(f"Unsupported transport type: {self.transport_type}")

    async def __aenter__(self):
        """Async context manager entry"""
        if not self._client:
            raise RuntimeError("Client not initialized")
            
        # When MCPClient is used as a context manager, enter the FastMCP client context
        self._context_manager = self._client.__aenter__()
        await self._context_manager
        
        # Get available tools after connection
        tools = await self.get_available_tools()
        print("\nConnected to server with tools:", [tool.name for tool in tools])
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._client:
            # Properly exit the FastMCP client context
            await self._client.__aexit__(exc_type, exc_val, exc_tb)

    async def cleanup(self):
        """Clean up resources"""
        if hasattr(self, '_context_manager') and self._client:
            # Properly exit the context manager
            await self._client.__aexit__(None, None, None)

    async def connect(self):
        """Establishes connection to MCP server using FastMCP"""
        if not self._client:
            raise RuntimeError("Client not initialized")
            
        # Enter the context manager properly for FastMCP client
        # This is a different approach than before - we need to actually start
        # using the client's context manager
        if not hasattr(self, '_context_manager'):
            self._context_manager = self._client.__aenter__()
            await self._context_manager
        
        # List available tools on connection
        tools = await self.get_available_tools()
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def get_available_tools(self) -> List[Any]:
        """
        Retrieve a list of available tools from the MCP server.
        """
        if not self._client:
            raise RuntimeError("Not connected to MCP server")
            
        async with self._client as client:
            tools = await client.list_tools()
            return tools

    def call_tool(self, tool_name: str) -> Any:
        """
        Create a callable function for a specific tool.
        This allows us to execute operations through the MCP server.

        Args:
            tool_name: The name of the tool to create a callable for

        Returns:
            A callable async function that executes the specified tool
        """
        if not self._client:
            raise RuntimeError("Not connected to MCP server")

        async def callable(*args, **kwargs):
            print("callable", tool_name, kwargs)
            
            # We need to use the async with context for each tool call to ensure proper connection
            async with self._client as client:
                result = await client.call_tool(tool_name, arguments=kwargs)
                
                # Handle the result structure from FastMCP
                if result and len(result) > 0:
                    # Extract data from the first content item
                    first_content = result[0]
                    if hasattr(first_content, "text") and first_content.text is not None:
                        return first_content.text
                    elif hasattr(first_content, "data") and first_content.data is not None:
                        return first_content.data
                
                return result  # Return full result if no content could be extracted

        return callable

    async def process_query(self, query: str, llm_client: Any = None) -> str:
        """
        Process a query using an LLM and available tools.
        
        Args:
            query: The query to process
            llm_client: Optional LLM client (e.g., Anthropic client) for processing
            
        Returns:
            Processed response as a string
        """
        if not llm_client:
            raise ValueError("LLM client is required for query processing")

        messages = [{"role": "user", "content": query}]

        # Get available tools in the format expected by the LLM
        tools = await self._client.list_tools()
        available_tools = [{
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in tools]

        # Initial LLM call
        response = llm_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=messages,
            tools=available_tools
        )

        # Process response and handle tool calls
        final_text = []
        assistant_message_content = []

        for content in response.content:
            if content.type == 'text':
                final_text.append(content.text)
                assistant_message_content.append(content)
            elif content.type == 'tool_use':
                tool_name = content.name
                tool_args = content.input

                # Execute tool call
                result = await self._client.call_tool(tool_name, tool_args)
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                assistant_message_content.append(content)
                messages.append({
                    "role": "assistant",
                    "content": assistant_message_content
                })
                
                # Format tool result for LLM
                tool_result_content = []
                for res_content in result:
                    if hasattr(res_content, "text"):
                        tool_result_content.append({"type": "text", "text": res_content.text})
                    elif hasattr(res_content, "data"):
                        tool_result_content.append({"type": "text", "text": str(res_content.data)})
                
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": content.id,
                            "content": tool_result_content
                        }
                    ]
                })

                # Get next response from LLM
                response = llm_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    messages=messages,
                    tools=available_tools
                )

                final_text.append(response.content[0].text)

        return "\n".join(final_text)