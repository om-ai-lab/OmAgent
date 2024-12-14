from typing import Dict, Any
from pathlib import Path
from typing import List
from pydantic import Field
from omagent_core.utils.registry import registry
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.engine.worker.base import BaseWorker

from omagent_core.models.llms.prompt.prompt import PromptTemplate
from omagent_core.tool_system.manager import ToolManager
from omagent_core.utils.logger import logging
import re

CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class ReActAgent(BaseLLMBackend, BaseWorker):
    
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
    tool_manager: ToolManager

    def _run(self, input_data, *args, **kwargs):
        """Implements one step of the ReAct cycle: Plan -> Act -> Observe"""
        # Plan the next action
        plan = self.plan(input_data)
        if not plan:
            return

        print(f"Plan: {plan}")
        
        # Execute the planned action
        result = self.act(plan)
        

        # If we got a final answer, we're done
        if  "final_answer" in plan:
            return result
            
        # Otherwise, observe the result and continue
        observation = self.observe(result)

        print(f"Observation: {observation}")
        #self._store_history(input_data, plan, observation)

        # return the join of plan and observation
        return f"Plan: {plan}\nObservation: {observation}"

    def should_stop(self, result: Any) -> bool:
        """Stop if the result is a final answer (string) rather than an observation"""
        return isinstance(result, str) and not "Observation:" in result
    
    def plan(self, task: str) -> Dict[str, Any]:        
        tool_descriptions = self.tool_manager.generate_prompt()
        
        #history = self._get_history_str()        
        history = ""
        print ("task:", task, "tool_descriptions:",tool_descriptions, "history:",history)
        response = self.simple_infer(task=task,
                tool_descriptions=tool_descriptions,
                history=history)
        
        print (response)
        return self._parse_response(response["choices"][0]["message"]["content"])
    
    def act(self, plan: Dict[str, Any]) -> Any:
        if not plan:
            return
            
        if "final_answer" in plan:
            return plan["final_answer"]
        
        tool_name = plan["tool_name"]
        tool_args = plan["tool_args"]
        
        # Debug: Check the tool schema
        print(f"Tool name: {tool_name}")
        print(f"Tool args before adjustment: {tool_args}")
        
        # Adjust `tool_args` if necessary
        for key, value in tool_args.items():
            if isinstance(value, list):
                # Flatten the list to a comma-separated string or adjust as needed
                tool_args[key] = ", ".join(value) if value else ""
        
        print(f"Tool args after adjustment: {tool_args}")
        
        # Execute the tool with adjusted arguments
        return self.tool_manager.execute(tool_name=tool_name, args=tool_args)
    
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
        
        try:
            if '(' not in action_line or ')' not in action_line:
                raise ValueError("Malformed action line: Missing parentheses.")
            tool_name = action_line[:action_line.index('(')].strip()
            args_str = action_line[action_line.index('(')+1:action_line.rindex(')')]
            
            # Parse arguments into a dictionary
            tool_args = {}
            if args_str:
                print ("args_str", args_str)
                tool_args = self.transform_input_to_output(args_str)
                """
                import ast
                for arg in args_str.split(','):
                    key, value = arg.split('=', 1)
                    # Ensure the value is a valid Python literal
                    value = value.strip()
                    # Handle list values correctly
                    if value.startswith('[') and value.endswith(']'):
                        tool_args[key.strip()] = ast.literal_eval(value)
                    else:
                        if not (value.startswith('"') and value.endswith('"')) and not (value.startswith("'") and value.endswith("'")):
                            value = f'"{value}"'  # Add quotes if missing
                        tool_args[key.strip()] = ast.literal_eval(value)
                """
            return {
                "tool_name": tool_name,
                "tool_args": tool_args
            }
        except Exception as e:            
            raise ValueError(f"Failed to parse tool call from response: {action_line}. Error: {str(e)}") from e
  
    def _get_history_str(self) -> str:
        """Retrieve the history of interactions."""
        workflow_instance_id = "react_agent_history"
        items = self.stm.items(workflow_instance_id)
        return "\n".join(f"Input: {item[0]}, Plan: {item[1]['plan']}, Observation: {item[1]['observation']}" for item in items)

    def _store_history(self, input_data: str, plan: Dict[str, Any], observation: str) -> None:
        """Store interaction history in STM."""
        workflow_instance_id = "react_agent_history"
        interaction = {"plan": plan, "observation": observation}
        self.stm[workflow_instance_id, input_data] = interaction

    def transform_input_to_output(self,input_text):        
        search_query = re.search(r'search_query="(.*?)"', input_text).group(1)        
        region = re.search(r'region="(.*?)"', input_text).group(1)
        num_results = int(re.search(r'num_results=(\d+)', input_text).group(1))
        
        goals_match = re.search(r'goals_to_browse=(\[.*?\]|".*?")', input_text)
        if goals_match:
            goals_raw = goals_match.group(1)
            if goals_raw.startswith('['):  # It's a list
                goals_to_browse = eval(goals_raw)
            else:  # It's a single string
                goals_to_browse = [goals_raw.strip('"')]
        else:
            goals_to_browse = ""
        # Construct output
        output = {

            "search_query": search_query,
            "region": region,
            "num_results": num_results,
            "goals_to_browse": goals_to_browse,

        }
        return output
    def get_tool_name(self, input_text):
        # Find the position of "Action:"
        action_start = input_text.find("Action:")
        if action_start == -1:
            return None  # Action not found
        
        # Extract the part of the text after "Action:"
        after_action = input_text[action_start + len("Action:"):].strip()
        
        # Split the string to isolate the tool name (first word before the parenthesis)
        tool_name = after_action.split('(')[0].strip()
        return tool_name
