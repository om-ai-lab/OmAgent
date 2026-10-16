

from pathlib import Path
from typing import List, Dict, Any

from omagent_core.advanced_components.workflow.dnc.schemas.dnc_structure import TaskTree
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.memories.ltms.ltm import LTM
from omagent_core.models.llms.base import BaseLLMBackend, BaseLLM
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
from openai import Stream
from pydantic import Field
from collections.abc import Iterator
from omagent_core.models.llms.prompt.parser import *
from omagent_core.tool_system.manager import ToolManager
import re
import json

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class Planner222(BaseLLMBackend, BaseWorker):
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(CURRENT_PATH.joinpath("planner_system.prompt"), role="system"),
            PromptTemplate.from_file(CURRENT_PATH.joinpath("planner_user.prompt"), role="user"),
        ]
    )
    llm: BaseLLM
    output_parser: DictParser = DictParser()
    tool_manager: ToolManager
    
    def _run(self, initial_description: str, *args, **kwargs):
        print("Input description:", initial_description)
        # Generate the initial plan.
        tool_schema = []
        for name, tool in self.tool_manager.tools.items():            
            tool_schema.append(str(tool.generate_schema()))

        tool_schema_str = "\n".join(tool_schema)
        self.stm(self.workflow_instance_id)["tool_schema"] = tool_schema_str
        plan_text = self.simple_infer(prompt=initial_description, tool_schema=tool_schema_str)["choices"][0]["message"].get("content")
        self.callback.info(agent_id=self.workflow_instance_id, progress="Planner", message=plan_text)
        state = self.stm(self.workflow_instance_id)
        state["plan"] = str(plan_text)

        state["initial_description"] = initial_description
        
        # Extract tool names from the plan
        tool_examples = self.generate_tool_examples(plan_text["tools"])
        state["tool_examples"] = tool_examples
        return {"plan": plan_text, "tool_examples": tool_examples}
        
    def generate_tool_examples(self, tools_list: List[str]) -> Dict[str, Any]:
        """Generate example tool calls and outputs based on the plan"""
        self.callback.info(agent_id=self.workflow_instance_id, progress="Planner", message="Generating tool examples...")
        
        
        # Clean and parse the tool names
        required_tools = []
        for tool_name, tool in self.tool_manager.tools.items():
            if tool_name in tools_list:
                required_tools.append((tool_name, tool))
                
        if not required_tools:
            self.callback.info(agent_id=self.workflow_instance_id, 
                              progress="No specific tools identified", 
                              message="Falling back to scanning plan text for tool mentions")
            
        # For each identified tool, generate a sample call and execute it
        tool_examples = {}
        print (required_tools)
        print (len(required_tools))
        for tool_name, tool in required_tools:  # Limit to 3 tools to avoid excessive calls
            try:                
                # Generate parameters for the tool based on the task description
                param_prompt = f"""
                Given this tool: {str(tool.generate_schema())}
                
                Generate a valid JSON object containing realistic parameters to call this tool.
                Only include the parameters, not the tool name or any explanation.
                """
                print (param_prompt)
                param_response = self.simple_infer(prompt=param_prompt)["choices"][0]["message"].get("content", "{}")
                
                # Extract the JSON
                param_match = re.search(r'```json\s*(.*?)\s*```', param_response, re.DOTALL)
                if param_match:
                    param_json = param_match.group(1)
                else:
                    param_json = param_response.strip()
                
                # Clean up any non-JSON content
                param_json = re.sub(r'^[^{]*', '', param_json)
                param_json = re.sub(r'[^}]*$', '', param_json)
                
                try:
                    params = json.loads(param_json)
                    
                    # Execute the tool call
                    self.callback.info(agent_id=self.workflow_instance_id, 
                                      progress=f"Testing tool: {tool_name}", 
                                      message=f"With params: {params}")
                    
                    # Execute the tool call
                    result =  self.tool_manager.execute(tool_name, params)
                    print (result)
                    # Save the example
                    tool_examples[tool_name] = {
                        "params": params,
                        "result": result
                    }
                    
                    self.callback.info(agent_id=self.workflow_instance_id, 
                                      progress=f"Tool example generated: {tool_name}", 
                                      message=f"Result: {result}")
                    
                except json.JSONDecodeError:
                    self.callback.info(agent_id=self.workflow_instance_id, 
                                     progress=f"Failed to parse parameters for {tool_name}", 
                                     message=f"Invalid JSON: {param_json}")
                except Exception as e:
                    self.callback.info(agent_id=self.workflow_instance_id, 
                                     progress=f"Failed to execute {tool_name}", 
                                     message=f"Error: {str(e)}")
            except Exception as e:
                self.callback.info(agent_id=self.workflow_instance_id, 
                                 progress=f"Error with tool {tool_name}", 
                                 message=f"Error: {str(e)}")
        
        return tool_examples
