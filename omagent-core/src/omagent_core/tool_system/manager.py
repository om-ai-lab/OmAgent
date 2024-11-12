import json
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

import yaml
from pydantic import Field, field_validator

from omagent_core.utils.logger import logging
from omagent_core.models.llms.schemas import Message
from omagent_core.utils.registry import registry
from omagent_core.models.llms.base import BaseLLM, BaseLLMBackend
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from .base import BaseTool
from omagent_core.base import BotBase

CURRENT_PATH = Path(__file__).parents[0]


class ToolManager(BaseLLMBackend):
    tools: Dict[str, BaseTool] = Field(
        default=registry.mapping["tool"], validate_default=True
    )
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

    @field_validator("tools", mode="before")
    @classmethod
    def init_tools(cls, tools: Union[List, Dict]) -> Dict[str, BaseTool]:
        if isinstance(tools, dict):
            for key, value in tools.items():
                if isinstance(value, type) and issubclass(value, BaseTool):
                    tools[key] = value = value()
                elif isinstance(value, dict):
                    tools[key] = value = registry.get_tool(key)(**value)
                elif not isinstance(value, BaseTool):
                    raise ValueError(
                        "The tool must be an instance of a sub class of BaseTool, not {}".format(
                            type(value)
                        )
                    )
                if key != value.name:
                    raise ValueError(
                        "The tool name {} not match with the tool {}.".format(
                            key, value.name
                        )
                    )
            return tools
        elif isinstance(tools, list):
            init_tools = {}
            for tool in tools:
                if isinstance(tool, str):
                    t = registry.get_tool(tool)
                    if isinstance(t, BaseTool):
                        init_tools[tool] = t
                    elif isinstance(t, type) and issubclass(t, BaseTool):
                        init_tools[tool] = t()
                    else:
                        raise ValueError("Invalid tool type {}".format(type(t)))
                elif isinstance(tool, dict):
                    t = registry.get_tool(tool["name"])
                    if isinstance(t, type) and issubclass(t, BaseTool):
                        init_tools[tool["name"]] = t(**tool)
                    else:
                        raise ValueError("Invalid tool type {}".format(type(t)))
                elif isinstance(tool, BaseTool):
                    init_tools[tool.name] = tool
                else:
                    raise ValueError("Invalid tool type {}".format(type(tool)))
            return init_tools
        else:
            raise ValueError(
                "Wrong tools type {}, should be list or dict in ToolManager".format(
                    type(tools)
                )
            )
    
    def model_post_init(self, __context: Any) -> None:
        for _, attr_value in self.__dict__.items():
            if isinstance(attr_value, BotBase):
                attr_value._parent = self
        for tool in self.tools.values():
            tool._parent = self
                
    @property 
    def workflow_instance_id(self) -> str:
        if hasattr(self, '_parent'):
            return self._parent.workflow_instance_id
        return None
        
    @workflow_instance_id.setter
    def workflow_instance_id(self, value: str):
        if hasattr(self, '_parent'):
            self._parent.workflow_instance_id = value

    def add_tool(self, tool: BaseTool):
        self.tools[tool.name] = tool

    def tool_names(self) -> List:
        return list(self.tools.keys())

    def generate_prompt(self):
        prompt = ""
        for index, (name, tool) in enumerate(self.tools.items()):
            prompt += f"{index + 1}. {name}: {tool.description}\n"
        return prompt

    def generate_schema(self, style: str = "gpt"):
        if style == "gpt":
            return [tool.generate_schema() for tool in self.tools.values()]
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

        return cls(**config)

    def execute_task(self, task, related_info='', function=None):
        if self.llm == None:
            raise ValueError(
                "The execute_task method requires the llm field to be initialized."
            )
        chat_complete_res = self.infer(
            [{"task": task, "related_info": related_info}],
            tools=self.generate_schema(),
        )[0]
        content = chat_complete_res["choices"][0]["message"].get("content")
        tool_calls = chat_complete_res["choices"][0]["message"].get("tool_calls")
        if not tool_calls:
            toolcall_failed_structure = {
                "status": "failed",
                "content": content,
            }
            return "failed", content
        else:
            tool_calls = [tool_calls[0]]
            toolcall_structure = {
                "name": tool_calls[0]["function"]["name"],
                "arguments": json.loads(tool_calls[0]["function"]["arguments"]),
            }
            self.callback.info(agent_id=self.workflow_instance_id, progress=f'Conqueror', message=f'Tool {toolcall_structure["name"]} executing.')
            tool_execution_res = []
            try:
                for each_tool_call in tool_calls:
                    tool_execution_res.append(
                        self.execute(
                            each_tool_call["function"]["name"],
                            each_tool_call["function"]["arguments"],
                        )
                    )

                toolcall_structure = {
                    "status": "success",
                    "tool_use": list(
                        set(
                            [
                                each_tool_call["function"]["name"]
                                for each_tool_call in tool_calls
                            ]
                        )
                    ),
                    "argument": [
                        eval(each_tool_call["function"]["arguments"])
                        for each_tool_call in tool_calls
                    ],
                }
                return "success", tool_execution_res
            except ValueError as error:
                toolcall_failed_structure = {
                    "status": "failed",
                    "tool_use": list(
                        set(
                            [
                                each_tool_call["function"]["name"]
                                for each_tool_call in tool_calls
                            ]
                        )
                    ),
                    "argument": [
                        each_tool_call["function"]["arguments"]
                        for each_tool_call in tool_calls
                    ],
                    "error": str(error),
                }
                return "failed", str(error)

    async def aexecute_task(self, task, related_info=None, function=None):
        if self.llm == None:
            raise ValueError(
                "The execute_task method requires the llm field to be initialized."
            )
        chat_complete_res = await self.ainfer(
            [{"task": task, "related_info": list(related_info.keys())}],
            tools=self.generate_schema(),
        )[0]
        content = chat_complete_res["choices"][0]["message"].get("content")
        tool_calls = chat_complete_res["choices"][0]["message"].get("tool_calls")
        if not tool_calls:
            toolcall_failed_structure = {
                "status": "failed",
                "content": content,
            }
            return "failed", content
        else:
            toolcall_structure = {
                "name": tool_calls[0]["function"]["name"],
                "arguments": json.loads(tool_calls[0]["function"]["arguments"]),
            }
            tool_execution_res = []
            try:
                for each_tool_call in tool_calls:
                    tool_execution_res.append(
                        await self.aexecute(
                            each_tool_call["function"]["name"],
                            each_tool_call["function"]["arguments"],
                        )
                    )

                toolcall_structure = {
                    "status": "success",
                    "tool_use": list(
                        set(
                            [
                                each_tool_call["function"]["name"]
                                for each_tool_call in tool_calls
                            ]
                        )
                    ),
                    "argument": [
                        eval(each_tool_call["function"]["arguments"])
                        for each_tool_call in tool_calls
                    ],
                }
                return "success", tool_execution_res
            except ValueError as error:
                toolcall_failed_structure = {
                    "status": "failed",
                    "tool_use": list(
                        set(
                            [
                                each_tool_call["function"]["name"]
                                for each_tool_call in tool_calls
                            ]
                        )
                    ),
                    "argument": [
                        each_tool_call["function"]["arguments"]
                        for each_tool_call in tool_calls
                    ],
                    "error": str(error),
                }
                return "failed", str(error)
