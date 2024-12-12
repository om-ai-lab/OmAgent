from typing import Dict, Any
from pathlib import Path
from typing import List

from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.utils.registry import registry
from omagent_core.models.llms.schemas import Message, Content
from omagent_core.utils.general import encode_image
from omagent_core.models.llms.prompt.parser import StrParser
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.engine.worker.base import BaseWorker, BaseLocalWorker
from omagent_core.utils.container import container

from pathlib import Path

from omagent_core.utils.registry import registry
from omagent_core.utils.general import read_image
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.logger import logging
from omagent_core.lite_engine.task import Task
from omagent_core.lite_engine.workflow import Workflow
from omagent_core.memories.stms.stm_redis import RedisSTM
from omagent_core.services.connectors.redis import RedisConnector
import re
import json_repair
from pathlib import Path
from typing import List
from pydantic import Field
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.engine.worker.base import BaseLocalWorker
from omagent_core.utils.registry import registry
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.utils.logger import logging
CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class ReActAgent(BaseLLMBackend, BaseLocalWorker):
    
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
    llm: OpenaiGPTLLM

    def _run(self, input_data, *args, **kwargs):
        """Implements one step of the ReAct cycle: Plan -> Act -> Observe"""
        # Plan the next action
        plan = self.plan(input_data)

        print(f"Plan: {plan}")
        
        # Execute the planned action
        result = self.act(plan)
        
        # If we got a final answer, we're done
        if "final_answer" in plan:
            return result
            
        # Otherwise, observe the result and continue
        observation = self.observe(result)

        print(f"Observation: {observation}")

        # return the join of plan and observation
        return f"Plan: {plan}\nObservation: {observation}"

    def should_stop(self, result: Any) -> bool:
        """Stop if the result is a final answer (string) rather than an observation"""
        return isinstance(result, str) and not "Observation:" in result
    
    def plan(self, task: str) -> Dict[str, Any]:
        tool_descriptions = "\n".join([
            f"- {tool.name}: {tool.description}" 
            for tool in self.tools
        ])
        
        history = self._get_history_str() if self.memory else ""
        response = self.simple_infer(task=task,
                tool_descriptions=tool_descriptions,
                history=history)
        
        
        return self._parse_response(response.content)
    
    def act(self, plan: Dict[str, Any]) -> Any:
        if "final_answer" in plan:
            return plan["final_answer"]
        
        tool_name = plan["tool_name"]
        tool_args = plan["tool_args"]
        
        tool = next(t for t in self.tools if t.name == tool_name)
        return tool(**tool_args)
    
    def observe(self, action_result: Any) -> str:
        return f"Observation: {action_result}"

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into either a tool call or final answer.
        
        Args:
            response (str): Raw response from LLM containing 'Thought' and 'Action'
            
        Returns:
            Dict[str, Any]: Dictionary containing either:
                - tool_name and tool_args for a tool call
                - final_answer for a direct response
        """
        # Extract the action line
        action_line = ""
        for line in response.split('\n'):
            if line.startswith('Action:'):
                action_line = line.replace('Action:', '').strip()
                break
        
        # Check if it's a final answer
        if action_line.startswith('Final Answer:'):
            return {
                "final_answer": response.split("Final Answer:")[1].strip()
            }
        
        # Parse tool call: tool_name(arg1=value1, arg2=value2)
        try:
            tool_name = action_line[:action_line.index('(')]
            args_str = action_line[action_line.index('(')+1:action_line.rindex(')')]
            
            # Parse arguments into a dictionary
            tool_args = {}
            if args_str:
                for arg in args_str.split(','):
                    key, value = arg.split('=')
                    tool_args[key.strip()] = value.strip()
            
            return {
                "tool_name": tool_name,
                "tool_args": tool_args
            }
        except Exception as e:
            raise ValueError(f"Failed to parse tool call from response: {action_line}") from e
        
    def _get_history_str(self) -> str:
        """Simply join the history with newlines"""
        return self.stm(self.workflow_instance_id).get('history', None)