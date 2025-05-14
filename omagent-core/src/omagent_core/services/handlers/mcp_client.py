import asyncio
import json
from typing import Any, Dict, List, Optional, Union
from contextlib import AsyncExitStack
import aiohttp


from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client

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

    def __init__(self, server_params: Union[StdioServerParameters, Dict[str, Any]], transport_type: str = TransportType.STDIO):
        """
        Initialize the MCP client with server parameters and transport type
        
        Args:
            server_params: For stdio, a StdioServerParameters object. For SSE, a dict with 'url' key
            transport_type: One of 'stdio' or 'sse'
        """
        self.server_params = server_params
        self.transport_type = transport_type

        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self._client = None
        self.stdio = None
        self.write = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

    async def connect(self):
        """Establishes connection to MCP server using the appropriate transport"""
        if self.transport_type == TransportType.STDIO:
            # STDIO transport
            self._client = stdio_client(self.server_params)
            stdio_transport = await self.exit_stack.enter_async_context(self._client)
            self.stdio, self.write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        elif self.transport_type == TransportType.SSE:
            # SSE transport
            if not isinstance(self.server_params, dict) or 'url' not in self.server_params:
                raise ValueError("SSE transport requires a dict with 'url' key in server_params")
            
            url = self.server_params['url']
            headers = self.server_params.get('headers', {})
            timeout = self.server_params.get('timeout', 30)
            
            # Create SSE client
            self._client = sse_client(url, headers=headers, timeout=timeout)
            sse_transport = await self.exit_stack.enter_async_context(self._client)
            self.stdio, self.write = sse_transport
            self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        else:
            raise ValueError(f"Unsupported transport type: {self.transport_type}")
        

        await self.session.initialize()

        # List available tools on connection
        tools = await self.get_available_tools()
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def get_available_tools(self) -> List[Any]:
        """
        Retrieve a list of available tools from the MCP server.
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
            
        response = await self.session.list_tools()
        tools = response.tools  # Direct access to tools from response
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
        if not self.session:
            raise RuntimeError("Not connected to MCP server")

        async def callable(*args, **kwargs):
            print ("callable", tool_name, kwargs)
            response = await self.session.call_tool(tool_name, arguments=kwargs)     
                   
            if hasattr(response, 'content') and response.content:
                #return response.content[0].dict()
                if hasattr(response.content[0], 'text'):
                    return response.content[0].text
                else:
                    return response.content[0].data

            return response  # Return full response if no content field

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
        response = await self.session.list_tools()
        available_tools = [{
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in response.tools]

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
                result = await self.session.call_tool(tool_name, tool_args)
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                assistant_message_content.append(content)
                messages.append({
                    "role": "assistant",
                    "content": assistant_message_content
                })
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": content.id,
                            "content": result.content
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