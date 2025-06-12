import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, ClassVar, Type, get_type_hints, Callable

import yaml
from omagent_core.base import BotBase
from omagent_core.models.llms.base import BaseLLM, BaseLLMBackend
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from omagent_core.models.llms.schemas import Message
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
from pydantic import Field, field_validator

from .base import BaseTool, ArgSchema
from omagent_core.services.handlers.mcp_utils import create_mcp_client, load_mcp_config, get_config_path, create_all_mcp_clients
from omagent_core.services.handlers.mcp_client import MCPClient
import asyncio
from PIL import Image
import base64
import io
import copy
from pprint import pprint

CURRENT_PATH = Path(__file__).parents[0]

# Separate adapter class for MCP tools that doesn't use Pydantic
class MCPToolAdapter:
    """Adapter class that wraps an MCP tool without using Pydantic inheritance."""
    
    def __init__(self, name: str, description: str, original_name: str, mcp_client: MCPClient, schema: Dict = None):
        self.name = name
        self.description = description
        self.original_name = original_name  # The original MCP tool name
        self.mcp_client = mcp_client
        self.schema = schema or {}
        self._parent = None
    
    async def run(self, **kwargs):
        """Execute the MCP tool with the given arguments."""
        if not self.mcp_client:
            raise ValueError("MCP client not initialized")
        
        try:
            # Extract actual arguments if they're nested under 'arguments' key
            actual_args = kwargs
            if 'arguments' in kwargs and isinstance(kwargs['arguments'], dict):
                actual_args = kwargs['arguments']
                print(f"Extracted nested arguments: {actual_args}")
            
            print(f"Calling MCP tool '{self.original_name}' with args: {actual_args}")
            result = await self.mcp_client.call_tool(self.original_name)(**actual_args)
            
            # Handle different types of content returned from MCP
            if hasattr(result, 'content') and isinstance(result.content, list) and len(result.content) > 0:
                content_item = result.content[0]
                print(f"MCP tool result: {content_item}")
                # Handle ImageContent specifically
                if hasattr(content_item, 'type') and content_item.type == 'image':
                    # For image content, return image data or URL
                    if hasattr(content_item, 'url'):
                        return {"type": "image", "url": content_item.url}
                    elif hasattr(content_item, 'data'):
                        return {"type": "image", "data": content_item.data}
                    else:
                        # Return a summary of what we have instead of failing
                        return {"type": "image", "summary": "Image data received but not accessible via text attribute"}
                
                # For standard text content
                if hasattr(content_item, 'text'):
                    return content_item.text
            
            # If we couldn't extract specific content format, return the whole result
            return result
        except Exception as e:
            print(f"Error in MCPToolAdapter run: {e}")
            # Return the error message rather than crashing
            return {"error": str(e), "status": "failed"}

    
    def generate_schema(self):
        """Generate a schema for the tool that's compatible with OpenAI's function calling format."""
        # Start with standard format structure
        schema = {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
        
        # If we have schema information, populate it
        if self.schema:
            required_params = []
            properties = {}
            
            for param_name, param_info in self.schema.items():
                # Create property entry
                property_entry = {
                    "type": param_info.get("type", "string"),
                    "description": param_info.get("description", f"Parameter {param_name}")
                }
                
                # Handle array type properties by adding an 'items' field
                if property_entry["type"] == "array":
                    # Add a default items schema if not specified
                    property_entry["items"] = param_info.get("items", {"type": "string"})
                
                # Add to properties dict
                properties[param_name] = property_entry
                
                # Check if required
                if param_info.get("required", False):
                    required_params.append(param_name)
            
            # Set properties and required fields
            schema["function"]["parameters"]["properties"] = properties
            schema["function"]["parameters"]["required"] = required_params
        else:
            # Default to a simple "input" parameter if no schema defined
            schema["function"]["parameters"]["properties"] = {
                "input": {
                    "type": "string",
                    "description": "Input for the tool"
                }
            }
            schema["function"]["parameters"]["required"] = ["input"]
        
        return schema
    
    @property
    def workflow_instance_id(self) -> str:
        if self._parent:
            return self._parent.workflow_instance_id
        return None


class ToolManager(BaseLLMBackend):
    # Instead of setting a default directly, which requires deep copying during model initialization
    # we'll use a post-init method to handle the tools initialization
    tools: Dict[str, Union[BaseTool, MCPToolAdapter]] = Field(default_factory=dict)
    llm: Optional[BaseLLM] = Field(default=None, validate_default=True)
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("sys_prompt.prompt"), role="system"
            ),
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("user_prompt.prompt"), role="user"
            ),
        ]
    )
    
    model_config = {
        "arbitrary_types_allowed": True,
        "protected_namespaces": (),
    }
    
    # Store mcp_client as a non-Pydantic attribute
    _mcp_client: Optional[MCPClient] = None
    
    def __init__(self, **data):
        # Handle mcp_client separately
        mcp_client = data.pop('mcp_client', None) if 'mcp_client' in data else None

        # Handle tools specially to avoid deep copying registry.mapping["tool"]
        if 'tools' not in data:
            # Initialize tools from registry if not provided
            tools_dict = {}
            for name, tool_cls in registry.mapping["tool"].items():
                print(f"tool_cls: {tool_cls}, {name}")
                try:
                    if isinstance(tool_cls, type) and issubclass(tool_cls, BaseTool):
                        tools_dict[name] = tool_cls()
                    elif isinstance(tool_cls, BaseTool):
                        tools_dict[name] = tool_cls
                except Exception as e:
                    print(f"Error in tool_cls: {e}")

            data['tools'] = tools_dict
        
        # Initialize Pydantic model first
        super().__init__(**data)
        
        # Then set mcp_client after Pydantic initialization
        self._mcp_client = mcp_client
    
    @property
    def mcp_client(self) -> Optional[MCPClient]:
        return self._mcp_client
        
    @mcp_client.setter
    def mcp_client(self, client: Optional[MCPClient]):
        self._mcp_client = client

    def __deepcopy__(self, memo):
        """Custom deepcopy that skips copying the mcp_client."""
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        
        # First ensure the Pydantic model is properly initialized
        # Create a dict of the fields to copy (excluding _mcp_client)
        fields_to_copy = {}
        for k, v in self.__dict__.items():
            if k != '_mcp_client':
                fields_to_copy[k] = copy.deepcopy(v, memo)
        
        # Initialize the object with the copied fields
        object.__setattr__(result, '__dict__', fields_to_copy)
        
        # Set the mcp_client without copying it
        result._mcp_client = self._mcp_client
        
        # Ensure Pydantic initialization attributes exist
        if hasattr(self, '__pydantic_fields_set__'):
            object.__setattr__(result, '__pydantic_fields_set__', 
                              copy.deepcopy(self.__pydantic_fields_set__, memo))
        
        if hasattr(self, '__pydantic_extra__'):
            object.__setattr__(result, '__pydantic_extra__',
                              copy.deepcopy(self.__pydantic_extra__, memo))
                              
        if hasattr(self, '__pydantic_private__'):
            object.__setattr__(result, '__pydantic_private__',
                              copy.deepcopy(self.__pydantic_private__, memo))
        
        return result

    def __copy__(self):
        """Custom copy that handles the mcp_client properly."""
        cls = self.__class__
        result = cls.__new__(cls)
        
        # Copy all attributes except _mcp_client
        for k, v in self.__dict__.items():
            if k != '_mcp_client':
                object.__setattr__(result, k, v)
        
        # Copy Pydantic special attributes if they exist
        if hasattr(self, '__pydantic_fields_set__'):
            object.__setattr__(result, '__pydantic_fields_set__', 
                              set(self.__pydantic_fields_set__))
        
        if hasattr(self, '__pydantic_extra__'):
            object.__setattr__(result, '__pydantic_extra__',
                              dict(self.__pydantic_extra__))
                              
        if hasattr(self, '__pydantic_private__'):
            object.__setattr__(result, '__pydantic_private__',
                              dict(self.__pydantic_private__))
        
        # Reference the original mcp_client
        result._mcp_client = self._mcp_client
        
        return result

    @field_validator("tools", mode="before")
    @classmethod
    def init_tools(cls, tools: Union[List, Dict]) -> Dict[str, Union[BaseTool, MCPToolAdapter]]:
        """Initialize tools from various formats while avoiding serialization issues."""
        if isinstance(tools, dict):
            # Make a shallow copy to avoid modifying the original
            tools_dict = {}
            
            for key, value in tools.items():
                if isinstance(value, type) and issubclass(value, BaseTool):
                    # Instantiate tool classes
                    tools_dict[key] = value()
                elif isinstance(value, dict):
                    # Create a tool from a config dictionary
                    tool_cls = registry.get_tool(key)
                    # Filter out mcp_client and mcp_config keys
                    tool_params = {k: v for k, v in value.items() 
                                 if k not in ["mcp_config"]}
                    tool_instance = tool_cls(**tool_params)

                    # Support MCP client config if present
                    if "mcp_config" in value:
                        # Load MCP client from config file
                        config_path = Path(value["mcp_config"]) if isinstance(value["mcp_config"], str) else None
                        mcp_client = create_mcp_client(config_path)
                        # Use direct attribute setting to avoid serialization
                        object.__setattr__(tool_instance, '_mcp_client', mcp_client)
                    
                    tools_dict[key] = tool_instance
                elif isinstance(value, BaseTool):
                    # Use existing tool instances as is
                    tools_dict[key] = value
                else:
                    raise ValueError(
                        f"The tool must be an instance of a subclass of BaseTool, not {type(value)}"
                    )
                    
                # Validate name consistency
                if key != tools_dict[key].name:
                    raise ValueError(
                        f"The tool name {key} does not match with the tool {tools_dict[key].name}"
                    )
            return tools_dict
        elif isinstance(tools, list):
            # Convert list to dictionary
            init_tools = {}
            for tool in tools:
                if isinstance(tool, str):
                    t = registry.get_tool(tool)
                    if isinstance(t, BaseTool):
                        init_tools[tool] = t
                    elif isinstance(t, type) and issubclass(t, BaseTool):
                        init_tools[tool] = t()
                    else:
                        raise ValueError(f"Invalid tool type {type(t)}")
                elif isinstance(tool, dict):
                    t = registry.get_tool(tool["name"])
                    if isinstance(t, type) and issubclass(t, BaseTool):
                        init_tools[tool["name"]] = t(**tool)
                    else:
                        raise ValueError(f"Invalid tool type {type(t)}")
                elif isinstance(tool, BaseTool):
                    init_tools[tool.name] = tool
                else:
                    raise ValueError(f"Invalid tool type {type(tool)}")
            return init_tools
        else:
            raise ValueError(
                f"Wrong tools type {type(tools)}, should be list or dict in ToolManager"
            )

    def model_post_init(self, __context: Any) -> None:
        for _, attr_value in self.__dict__.items():
            if isinstance(attr_value, BotBase):
                attr_value._parent = self
        for tool in self.tools.values():
            tool._parent = self
            
        # Auto-initialize MCP if there's a config file
        try:
            if self.mcp_client is None:
                # Try to find MCP config in the tool_system directory
                mcp_config_path = CURRENT_PATH.joinpath("mcp.json")
                if mcp_config_path.exists():
                    print(f"Auto-initializing MCP from {mcp_config_path}")
                    self.initialize_mcp(config_path=mcp_config_path)
                else:
                    # Fall back to standard config paths
                    mcp_config_path = get_config_path()
                    if mcp_config_path.exists():
                        print(f"Auto-initializing MCP from {mcp_config_path}")
                        self.initialize_mcp(config_path=mcp_config_path)
        except Exception as e:
            print(f"Failed to auto-initialize MCP: {e}")

    @property
    def workflow_instance_id(self) -> str:
        if hasattr(self, "_parent"):
            return self._parent.workflow_instance_id
        return None

    @workflow_instance_id.setter
    def workflow_instance_id(self, value: str):
        if hasattr(self, "_parent"):
            self._parent.workflow_instance_id = value

    def add_tool(self, tool: Union[BaseTool, MCPToolAdapter]):
        self.tools[tool.name] = tool

    def tool_names(self) -> List:
        return list(self.tools.keys())

    def generate_prompt(self):
        prompt = ""
        for index, (name, tool) in enumerate(self.tools.items()):
            prompt += f"{index + 1}. {name}: {tool.description}\n"
        return prompt

    def _standardize_tool_schema(self, tool):
        """Standardize tool schema to ensure consistent format for OpenAI API."""
        schema = tool.generate_schema()
        
        # Ensure schema has proper structure
        if "type" not in schema:
            schema["type"] = "function"
            
        if "function" not in schema:
            # Move any top-level attributes to function
            if "description" in schema:
                desc = schema.pop("description")
            else:
                desc = getattr(tool, "description", f"Tool: {tool.name}")
                
            schema["function"] = {
                "name": tool.name,
                "description": desc
            }
        
        # Ensure function has name and description
        if "name" not in schema["function"]:
            schema["function"]["name"] = tool.name
            
        if "description" not in schema["function"]:
            schema["function"]["description"] = getattr(tool, "description", f"Tool: {tool.name}")
        
        # Ensure parameters field exists and is properly structured
        if "parameters" not in schema["function"]:
            schema["function"]["parameters"] = {
                "type": "object",
                "properties": {},
                "required": []
            }
        
        # Ensure parameters has type, properties, and required fields
        params = schema["function"]["parameters"]
        if "type" not in params:
            params["type"] = "object"
            
        if "properties" not in params:
            params["properties"] = {}
            
        if "required" not in params:
            params["required"] = []
        
        return schema

    def generate_schema(self, style: str = "gpt"):
        if style == "gpt":
            tool_schemas = []
            for tool in self.tools.values():
                # Use the standardization method to ensure consistent format
                schema = self._standardize_tool_schema(tool)
                
                # Add required fields if missing for OpenAI compatibility
                if "function" in schema:
                    func_schema = schema["function"]
                    
                    # Ensure parameters are properly structured
                    if "parameters" not in func_schema:
                        func_schema["parameters"] = {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                        
                    # Ensure required is an array
                    if "required" not in func_schema["parameters"]:
                        func_schema["parameters"]["required"] = []
                        
                    # Ensure parameters has properties
                    if "properties" not in func_schema["parameters"]:
                        func_schema["parameters"]["properties"] = {}
                
                tool_schemas.append(schema)

            return tool_schemas
        else:
            raise ValueError("Only support gpt style tool selection schema")

    def execute(self, tool_name: str, args: Union[str, dict]):
        if tool_name not in self.tools:
            raise KeyError(f"The tool {tool_name} is invalid, not in the tool list.")
        tool = self.tools.get(tool_name)
        
        if type(args) is str:
            try:
                args = json.loads(args)
            except Exception as error:
                if self.llm is not None:
                    try:
                        args = self.dynamic_json_fixs(
                            args, tool.generate_schema(), [], str(error)
                        )
                        args = json.loads(args)
                    except:
                        raise ValueError(
                            "The args for tool execution is not a valid json string and can not be fixed. [{}]".format(
                                args
                            )
                        )

                else:
                    raise ValueError(
                        "The args for tool execution is not a valid json string. [{}]".format(
                            args
                        )
                    )
        
        # Handle nested arguments structure (e.g., {"arguments": {...}, "name": "tool_name"})
        if isinstance(args, dict) and "arguments" in args and isinstance(args["arguments"], dict):
            print(f"Extracting nested arguments structure for tool {tool_name}")
            args = args["arguments"]


        # Handle MCPToolAdapter separately
        if isinstance(tool, MCPToolAdapter):
            print("MCPToolAdapter")
            # Create an async handler to safely execute the async task
            async def run_async_tool():
                try:
                    return await tool.run(**args)
                except Exception as e:
                    print(f"Error in MCPToolAdapter execution: {e}")
                    raise
            
            # Create a new event loop if needed
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    raise RuntimeError("Event loop is closed")
            except RuntimeError:
                # If no loop exists or it's closed, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            print("Running MCPToolAdapter with asyncio")
            try:
                # Run with a timeout
                result = loop.run_until_complete(
                    asyncio.wait_for(run_async_tool(), timeout=200.0)
                )
                print("MCPToolAdapter execution completed successfully")
                return result
            except asyncio.TimeoutError:
                print("MCPToolAdapter execution timed out")
                return "Tool execution timed out after 60 seconds"
            except Exception as e:
                print(f"Error during MCPToolAdapter execution: {e}")
                raise
        else:
            print("BaseTool")
            # Standard BaseTool handling
            if tool.args_schema != None:
                args = tool.args_schema.validate_args(args)
            return tool.run(args)

    async def aexecute(self, tool_name: str, args: Union[str, dict]):
        if tool_name not in self.tools:
            raise KeyError(f"The tool {tool_name} is invalid, not in the tool list.")
        tool = self.tools.get(tool_name)
        
        if type(args) is str:
            try:
                args = json.loads(args)
            except Exception as error:
                if self.llm is not None:
                    try:
                        args = self.dynamic_json_fixs(
                            args, tool.generate_schema(), [], str(error)
                        )
                        args = json.loads(args)
                    except:
                        raise ValueError(
                            "The args for tool execution is not a valid json string and can not be fixed. [{}]".format(
                                args
                            )
                        )

                else:
                    raise ValueError(
                        "The args for tool execution is not a valid json string. [{}]".format(
                            args
                        )
                    )
        
        # Handle nested arguments structure (e.g., {"arguments": {...}, "name": "tool_name"})
        if isinstance(args, dict) and "arguments" in args and isinstance(args["arguments"], dict):
            print(f"Extracting nested arguments structure for tool {tool_name}")
            args = args["arguments"]
                    
        # Handle MCPToolAdapter separately
        if isinstance(tool, MCPToolAdapter):
            print(f"Executing async MCPToolAdapter {tool_name} with args: {args}")

            return await tool.run(**args)
        else:
            # Standard BaseTool handling
            if tool.args_schema != None:
                args = tool.args_schema.validate_args(args)
            return await tool.arun(args)

    def dynamic_json_fixs(
        self,
        broken_json,
        function_schema,
        messages: list = [],
        error_message: str = None,
    ):
        logging.warning(
            "Schema Validation for Function call {} failed, trying to fix it...".format(
                function_schema["name"]
            )
        )
        messages = [
            *messages,
            {
                "role": "system",
                "content": "\n".join(
                    [
                        "Your last function call result in error",
                        "--- Error ---",
                        error_message,
                        "Your task is to fix all errors exist in the Broken Json String to make the json validate for the schema in the given function, and use new string to call the function again.",
                        "--- Notice ---",
                        "- You need to carefully check the json string and fix the errors or adding missing value in it.",
                        "- Do not give your own opinion or imaging new info or delete exisiting info!",
                        "- Make sure the new function call does not contains information about this fix task!",
                        "--- Broken Json String ---",
                        broken_json,
                        "Start!",
                    ]
                ),
            },
        ]
        fix_res = self.llm.generate(
            records=[Message(**item) for item in messages], tool_choice=function_schema
        )
        return fix_res["choices"][0]["message"]["tool_calls"][0]["function"][
            "arguments"
        ]

    @classmethod
    def from_file(cls, file: Union[str, Path]):
        if type(file) is str:
            file = Path(file)
        elif type(file) is not Path:
            raise ValueError("Only support str or pathlib.Path")
        if not file.exists():
            raise FileNotFoundError("The file {} is not exists.".format(file))
        if file.suffix == ".json":
            config = json.load(open(file, "r"))
        elif file.suffix in (".yaml", ".yml"):
            config = yaml.load(open(file, "r"), Loader=yaml.FullLoader)
        else:
            raise ValueError("Only support json or yaml file.")

        # Extract and remove mcp_config from the main config if present
        mcp_config = config.pop("mcp_config", None)
        
        # Create the tool manager
        tool_manager = cls(**config)
        
        # Initialize MCP with provided config if present
        if mcp_config:
            if isinstance(mcp_config, str):
                mcp_config_path = Path(mcp_config)
                tool_manager.initialize_mcp(mcp_config_path)
            else:
                # Create a temporary config file
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    json.dump({"mcpServers": {"default": mcp_config}}, f)
                    temp_path = Path(f.name)
                tool_manager.initialize_mcp(temp_path)
                # Clean up the temporary file
                temp_path.unlink()
        else:
            # Try auto-initializing MCP from standard locations
            try:
                mcp_config_path = get_config_path()
                if mcp_config_path.exists():
                    tool_manager.initialize_mcp(mcp_config_path)
            except Exception as e:
                logging.warning(f"Failed to auto-initialize MCP: {e}")
        
        # Return the tool manager instead of exiting
        return tool_manager

    def execute_task(self, task, related_info="", function=None):
        if self.llm == None:
            raise ValueError(
                "The execute_task method requires the llm field to be initialized."
            )
        
        # Format related_info as string if it's a dictionary
        if isinstance(related_info, dict):
            related_info_str = "\n".join([f"{k}: {v}" for k, v in related_info.items()])
        else:
            related_info_str = str(related_info)
            
        print("Task:", task)
        print("Related info:", related_info_str)
        
        # Get standardized tool schemas
        tools_schema = self.generate_schema()
        print(f"Found {len(tools_schema)} available tools")
        
        # Create a more structured system prompt that uses XML tags for tools
        tool_schemas_str = json.dumps(tools_schema)
        
        system_prompt = f"""You are a function calling AI model. You are provided with function signatures within <tools></tools> XML tags. You may call one or more functions to assist with the user query. Don't make assumptions about what values to plug into functions. Here are the available tools: <tools> {tool_schemas_str} </tools> Use the following pydantic model json schema for each tool call you will make: {{"properties": {{"arguments": {{"title": "Arguments", "type": "object"}}, "name": {{"title": "Name", "type": "string"}}}}, "required": ["arguments", "name"], "title": "FunctionCall", "type": "object"}} For each function call return a json object with function name and arguments within <tool_call></tool_call> XML tags as follows:
<tool_call>
{{"arguments": <args-dict>, "name": <function-name>}}
</tool_call>"""
        
        # Prepare messages with explicit tool-use instructions
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Task: {task}\nContext: {related_info_str}"}
        ]
        
        try:
            # Call the LLM with the structured prompt
            print("Calling LLM with structured prompt for tool calling")
            chat_complete_res = self.llm.generate(
                records=[Message(**item) for item in messages],
                tools=tools_schema,
                tool_choice="auto"
            )
            
            print("Response received")
            
            # Extract content from response
            content = chat_complete_res["choices"][0]["message"].get("content", "")
            tool_calls = chat_complete_res["choices"][0]["message"].get("tool_calls", [])
            
            print("Tool calls directly from API:", "Yes" if tool_calls else "No")
                        
            
            # If API didn't return tool_calls, try to parse from content
            if not tool_calls and content:
                print("No tool_calls in API response, trying to extract from content")
                tool_name, args = self._extract_tool_call_json(content)
                print(tool_name, args)
                if tool_name and args:
                    print(f"Executing extracted tool: {tool_name}")
                    print(f"With arguments: {args}")
                    
                    # Execute the tool with the provided arguments
                    try:
                        result = self.execute(tool_name, args)
                        return "success", result
                    except Exception as e:
                        error_msg = f"Error executing tool {tool_name}: {str(e)}"
                        print(error_msg)
                        return "failed", error_msg
            
            # If we have tool_calls directly from API, use them
            if tool_calls:
                # Process the first tool call
                tool_call = tool_calls[0]
                print("tool_call:", tool_call)
                tool_name = tool_call["function"]["name"]
                
                try:
                    # Parse the arguments
                    args = json.loads(tool_call["function"]["arguments"])
                except json.JSONDecodeError as e:
                    print(f"Error parsing arguments: {e}")
                    args = tool_call["function"]["arguments"]
                    
                print(f"Executing tool from API: {tool_name}")
                print(f"With arguments: {args}")
                
                try:
                    # Execute the tool with the provided arguments
                    result = self.execute(tool_name, args)
                    return "success", result
                except Exception as e:
                    error_msg = f"Error executing tool {tool_name}: {str(e)}"
                    print(error_msg)
                    return "failed", error_msg
            
            # If we reach here, no tool calls were found or processed
            print("No tool calls could be found or processed. Model responded with:", content)
            return "failed", content
            
        except Exception as e:
            error_msg = f"LLM call failed: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return "failed", error_msg
       

    async def aexecute_task(self, task, related_info=None, function=None):
        if self.llm == None:
            raise ValueError(
                "The execute_task method requires the llm field to be initialized."
            )
        
        if isinstance(related_info, dict):
            related_info_str = "\n".join([f"{k}: {v}" for k, v in related_info.items()])
        else:
            related_info_str = str(related_info)
            
        print("Task:", task)
        print("Related info:", related_info_str)
        
        # Get standardized tool schemas
        tools_schema = self.generate_schema()
        print(f"Found {len(tools_schema)} available tools")
        
        # Create a more structured system prompt that uses XML tags for tools
        tool_schemas_str = json.dumps(tools_schema)
        
        system_prompt = f"""You are a function calling AI model. You are provided with function signatures within <tools></tools> XML tags. You may call one or more functions to assist with the user query. Don't make assumptions about what values to plug into functions. Here are the available tools: <tools> {tool_schemas_str} </tools> Use the following pydantic model json schema for each tool call you will make: {{"properties": {{"arguments": {{"title": "Arguments", "type": "object"}}, "name": {{"title": "Name", "type": "string"}}}}, "required": ["arguments", "name"], "title": "FunctionCall", "type": "object"}} For each function call return a json object with function name and arguments within <tool_call></tool_call> XML tags as follows:
<tool_call>
{{"arguments": <args-dict>, "name": <function-name>}}
</tool_call>"""
        
        # Prepare messages with explicit tool-use instructions
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Task: {task}\nContext: {related_info_str}"}
        ]
        
        try:
            # Call the LLM with the structured prompt
            print("Calling LLM with structured prompt for tool calling")
            chat_complete_res = await self.llm.agenerate(
                records=[Message(**item) for item in messages],
                tools=tools_schema,
                tool_choice="auto"
            )
            
            print("Response received")
            
            if not chat_complete_res or len(chat_complete_res["choices"]) == 0:
                return "failed", "No response from LLM"
            
            # Extract content from response
            content = chat_complete_res["choices"][0]["message"].get("content", "")
            tool_calls = chat_complete_res["choices"][0]["message"].get("tool_calls", [])
            
            print("Tool calls directly from API:", "Yes" if tool_calls else "No")
            
            # If API didn't return tool_calls, try to parse from content
            
            if not tool_calls and content:
                print("No tool_calls in API response, trying to extract from content")
                
                tool_name, args = self._extract_tool_call_json(content)
                
                if tool_name and args:
                    print(f"Executing extracted tool: {tool_name}")
                    print(f"With arguments: {args}")
                    
                    # Execute the tool with the provided arguments
                    try:
                        result = await self.aexecute(tool_name, args)
                        return "success", result
                    except Exception as e:
                        error_msg = f"Error executing tool {tool_name}: {str(e)}"
                        print(error_msg)
                        return "failed", error_msg
            
            # If we have tool_calls directly from API, use them
            if tool_calls:
                # Process the first tool call
                tool_call = tool_calls[0]
                print("tool_call:", tool_call)
                tool_name = tool_call["function"]["name"]
                
                try:
                    args = json.loads(tool_call["function"]["arguments"])
                except json.JSONDecodeError as e:
                    print(f"Error parsing arguments: {e}")
                    args = tool_call["function"]["arguments"]
                
                print(f"Executing tool from API: {tool_name}")
                print(f"With arguments: {args}")
                
                try:
                    # Execute the tool
                    result = await self.aexecute(tool_name, args)
                    return "success", result
                except Exception as e:
                    error_msg = f"Error executing tool {tool_name}: {str(e)}"
                    print(f"Tool execution error: {error_msg}")
                    return "failed", error_msg
            
            # If we reach here, no tool calls were found or processed
            print("No tool calls could be found or processed. Model responded with:", content)
            return "failed", content
            
        except Exception as e:
            error_msg = f"LLM call failed: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return "failed", error_msg

    def initialize_mcp(self, config_path: Optional[Path] = None, server_names: Optional[List[str]] = None):
        """
        Initialize MCP clients for the ToolManager and all tools.
        
        Args:
            config_path: Path to the MCP config file
            server_names: List of specific servers to use from the config. If None, will use all servers.
        """
        # Create the MCP clients
        mcp_clients = create_all_mcp_clients(config_path)
        
        if not mcp_clients:
            print("No valid MCP clients could be created from config")
            return self
        
        # Filter to specific servers if requested
        if server_names:
            mcp_clients = {name: client for name, client in mcp_clients.items() if name in server_names}
        
        # Set the default MCP client (first one in the dict)
        if mcp_clients:
            default_server = next(iter(mcp_clients.keys()))
            self.mcp_client = mcp_clients[default_server]
            print(f"Set default MCP client to '{default_server}'")
        
        # Store all clients
        self._mcp_clients = mcp_clients
        
        # Discover and register MCP tools asynchronously from all servers
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # Create a new event loop if there isn't one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        loop.run_until_complete(self.discover_all_mcp_tools())
        return self

    async def discover_all_mcp_tools(self):
        """
        Discover available tools from all configured MCP servers and register them.
        """
        if not hasattr(self, '_mcp_clients') or not self._mcp_clients:
            print("No MCP clients configured")
            return self
        
        for server_name, client in self._mcp_clients.items():
            print(f"Discovering tools from MCP server: {server_name}")
            await self.discover_mcp_tools_from_client(server_name, client)
        
        return self
    
    async def discover_mcp_tools_from_client(self, server_name: str, client: MCPClient):
        """
        Discover available tools from a specific MCP client and register them.
        
        Args:
            server_name: Name of the MCP server
            client: The MCPClient instance
        """
        if not client:
            print(f"MCP client '{server_name}' is invalid")
            return
        
        try:
            # Use the proper async with context manager pattern that FastMCP requires
            async with client._client as fastmcp_client:
                # Get available tools from MCP server
                available_tools = await fastmcp_client.list_tools()
                
                for tool in available_tools:
                    # Create a sanitized tool name with server prefix
                    base_name = tool.name.replace('-', '_').replace(' ', '_').lower()
                    # Include server name in the tool name to avoid conflicts between servers
                    tool_name = f"mcp_{server_name}_{base_name}"
                    #print(f"Discovered MCP tool: {tool_name}")
                    
                    # Skip if tool already exists
                    if tool_name in self.tools:
                        continue
                        
                    # Create a schema from MCP tool's input schema
                    schema_dict = {}
                    if hasattr(tool, 'inputSchema') and tool.inputSchema:
                        if 'properties' in tool.inputSchema:
                            for prop_name, prop_info in tool.inputSchema['properties'].items():
                                # Create property info with type and description
                                property_info = {
                                    "description": prop_info.get("description", f"Parameter {prop_name}"),
                                    "type": prop_info.get("type", "string"),
                                    "required": prop_name in tool.inputSchema.get('required', [])
                                }
                                
                                # Handle array type properties
                                if property_info["type"] == "array" and "items" in prop_info:
                                    property_info["items"] = prop_info["items"]
                                
                                # Add enums if present
                                if "enum" in prop_info:
                                    property_info["enum"] = prop_info["enum"]
                                    
                                schema_dict[prop_name] = property_info
                    
                    # Get description with fallback and include server name
                    tool_description = getattr(tool, 'description', None) or f"MCP tool: {tool.name}"
                    tool_description = f"[{server_name}] {tool_description}"
                    
                    # Create the adapter
                    dynamic_tool = MCPToolAdapter(
                        name=tool_name,
                        description=tool_description,
                        original_name=tool.name,
                        mcp_client=client,
                        schema=schema_dict
                    )
                    
                    # Set the parent for workflow ID
                    dynamic_tool._parent = self
                    
                    # Register the tool
                    self.add_tool(dynamic_tool)
                    
        except Exception as e:
            print(f"Error discovering MCP tools from '{server_name}': {e}")
            
        return self

    async def discover_mcp_tools(self):
        """
        Discover available tools from the default MCP server and register them.
        This method is kept for backward compatibility.
        """
        if not self.mcp_client:
            print("No default MCP client configured")
            return self
            
        try:
            # Use the proper async with context manager pattern that FastMCP requires
            async with self.mcp_client._client as fastmcp_client:
                # Get available tools from MCP server
                available_tools = await fastmcp_client.list_tools()
                
                for tool in available_tools:
                    # Create a sanitized tool name
                    base_name = tool.name.replace('-', '_').replace(' ', '_').lower()
                    tool_name = f"mcp_{base_name}"
                    print(f"Discovered MCP tool: {tool_name}")
                    
                    # Skip if tool already exists
                    if tool_name in self.tools:
                        continue
                        
                    # Create a schema from MCP tool's input schema
                    schema_dict = {}
                    if hasattr(tool, 'inputSchema') and tool.inputSchema:
                        if 'properties' in tool.inputSchema:
                            for prop_name, prop_info in tool.inputSchema['properties'].items():
                                # Create property info with type and description
                                property_info = {
                                    "description": prop_info.get("description", f"Parameter {prop_name}"),
                                    "type": prop_info.get("type", "string"),
                                    "required": prop_name in tool.inputSchema.get('required', [])
                                }
                                
                                # Handle array type properties
                                if property_info["type"] == "array" and "items" in prop_info:
                                    property_info["items"] = prop_info["items"]
                                
                                # Add enums if present
                                if "enum" in prop_info:
                                    property_info["enum"] = prop_info["enum"]
                                    
                                schema_dict[prop_name] = property_info
                    
                    # Get description with fallback to ensure it's not None
                    tool_description = getattr(tool, 'description', None) or f"MCP tool: {tool.name}"
                    
                    # Create the adapter
                    dynamic_tool = MCPToolAdapter(
                        name=tool_name,
                        description=tool_description,
                        original_name=tool.name,
                        mcp_client=self.mcp_client,
                        schema=schema_dict
                    )
                    
                    # Set the parent for workflow ID
                    dynamic_tool._parent = self
                    
                    # Register the tool
                    self.add_tool(dynamic_tool)
                
        except Exception as e:
            print(f"Error discovering MCP tools: {e}")
            
        return self

    def _check_tool_media_support(self, tool, media_type):
        """Check if a tool supports the given media type."""
        # Simple heuristic based on tool name and description
        if not tool.args_schema:
            return False
        
        schema_fields = tool.args_schema.model_dump().keys() if tool.args_schema else []
        
        # Look for common parameter names that might indicate media support
        media_keywords = {
            "image": ["image", "img", "photo", "picture", "screenshot"],
            "video": ["video", "movie", "clip", "footage"],
            "audio": ["audio", "sound", "recording", "voice"]
        }
        
        # Check tool description and schema fields for media-related terms
        description_lower = tool.description.lower()
        for keyword in media_keywords.get(media_type, []):
            if keyword in description_lower:
                return True
        
        for field in schema_fields:
            for keyword in media_keywords.get(media_type, []):
                if keyword in field.lower():
                    return True
        
        return False

    def _encode_image(self, image: Image.Image) -> str:
        """Encode an image to base64."""
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def _process_media_parameters(self, parameters, media, media_type):
        """Process parameters to include media content where needed."""
        if media is None:
            return parameters
        
        # Deep copy to avoid modifying the original
        processed_params = copy.deepcopy(parameters)
        
        # Convert placeholders to actual media
        for key, value in processed_params.items():
            if isinstance(value, str) and "MEDIA_PLACEHOLDER" in value:
                if media_type == "image":
                    if isinstance(media, list):
                        # For multiple images, encode them all and include as a list
                        processed_params[key] = [self._encode_image(img) for img in media]
                    else:
                        # Single image
                        processed_params[key] = self._encode_image(media)
                elif media_type in ["video", "audio"]:
                    # For video/audio, just include the file path
                    processed_params[key] = media
        
    def _extract_tool_call_json(self, content: str):
        """Extract tool call JSON from content regardless of surrounding tags or formats.
        
        Args:
            content: String that might contain a tool call JSON
            
        Returns:
            Tuple of (tool_name, args) if successful, or (None, None) if not
        """
        if not content or not isinstance(content, str):
            return None, None
            
        print(f"Extracting tool call from content: {content[:200]}")
        
        
        # First clean up the content by removing any HTML/XML tags
        import re
        
        # Try to find a JSON object with "arguments" and "name" keys
        try:
            # Clean up the content by stripping any text before the first { and after the last }
            first_brace = content.find('{')
            last_brace = content.rfind('}')
            
            if first_brace >= 0 and last_brace > first_brace:
                json_str = content[first_brace:last_brace+1]
                try:
                    # Try to parse the JSON
                    json_data = json.loads(json_str)
                    if isinstance(json_data, dict) and "name" in json_data and "arguments" in json_data:
                        return json_data["name"], json_data["arguments"]
                except:
                    pass
                
            # If the above approach failed, try a more aggressive regex approach to find JSON
            # Find anything that looks like a JSON object
            json_pattern = r'\{(?:[^{}]|"[^"]*"|\{(?:[^{}]|"[^"]*")*\})*\}'
            json_matches = re.findall(json_pattern, content, re.DOTALL)
            
            # Try each potential JSON match
            for json_str in json_matches:
                try:
                    json_data = json.loads(json_str)
                    if isinstance(json_data, dict):
                        # Check if it has name and arguments fields
                        if "name" in json_data and "arguments" in json_data:
                            print(f"Found valid tool call JSON with name:{json_data['name']}")
                            return json_data["name"], json_data["arguments"]
                except:
                    continue
                    
            # If still no match, try to find JSON-like patterns with manually specified patterns
            print("Trying specialized JSON extraction patterns...")
            
            # Look for patterns like "name": "something", "arguments": {...}
            name_pattern = r'"name"\s*:\s*"([^"]+)"'
            args_pattern = r'"arguments"\s*:\s*(\{[^}]+\})'
            
            name_match = re.search(name_pattern, content)
            args_match = re.search(args_pattern, content)
            
            if name_match and args_match:
                tool_name = name_match.group(1)
                args_str = args_match.group(1)
                try:
                    args = json.loads(args_str)
                    print(f"Extracted tool name '{tool_name}' and arguments from separate patterns")
                    return tool_name, args
                except:
                    pass
                    
            # Last resort: handle the specific issue with tool calls that don't follow JSON format
            if '</SOLUTION>' in content:
                # Edge case for weird formatting like '</SOLUTION>\n{"arguments": {...}, "name": "..."}'
                clean_content = content.replace('</SOLUTION>', '').strip()
                try:
                    json_data = json.loads(clean_content)
                    if "name" in json_data and "arguments" in json_data:
                        return json_data["name"], json_data["arguments"]
                except:
                    pass
                    
            # If we still haven't found a match, check if any tool name appears in the content
            for tool_name in self.tools.keys():
                if tool_name in content:
                    # Extract JSON-looking parts of the content
                    json_candidates = re.findall(r'\{.*?\}', content, re.DOTALL)
                    for json_str in json_candidates:
                        try:
                            args = json.loads(json_str)
                            if isinstance(args, dict):
                                print(f"Found potential arguments for tool '{tool_name}'")
                                return tool_name, args
                        except:
                            continue
                            
        except Exception as e:
            print(f"Error during JSON extraction: {e}")
            import traceback
            traceback.print_exc()
            
        return None, None
