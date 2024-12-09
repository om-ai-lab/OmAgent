import json_repair
import re
from pathlib import Path
from typing import List

from pydantic import Field

from omagent_core.utils.registry import registry
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from omagent_core.tool_system.manager import ToolManager  
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.prompt.parser import StrParser
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.utils.logger import logging

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class BodyAnalysisQA(BaseLLMBackend, BaseWorker):
    
    llm: OpenaiGPTLLM
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("sys_prompt_en.prompt"), role="system"
            ),
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("user_prompt_en.prompt"), role="user"
            ),
        ]
    )
    tool_manager: ToolManager
    
    def _run(self, *args, **kwargs):
        
        
        # Retrieve conversation context from memory, initializing empty if not present
        if self.stm(self.workflow_instance_id).get("user_body_data"):   
            if isinstance(self.stm(self.workflow_instance_id).get("user_body_data"),str):
                user_body_data = [self.stm(self.workflow_instance_id).get("user_body_data")]
            else:
                user_body_data = self.stm(self.workflow_instance_id).get("user_body_data")
        else:
            user_body_data = []
        
        # if self.stm(self.workflow_instance_id).get("other_body_info"):
        #     other_body_info = self.stm(self.workflow_instance_id).get("other_body_info")
        # else:
        #     other_body_info = []
            
        if self.stm(self.workflow_instance_id).get("search_info"):
            search_info = self.stm(self.workflow_instance_id).get("search_info")
        else:
            search_info = []
        
        if self.stm(self.workflow_instance_id).get("feedback"):
            feedback = self.stm(self.workflow_instance_id).get("feedback")
        else:
            feedback = []

        # Log current conversation state for debugging
        chat_structure = {
            "user_body_data": user_body_data,
            # "other_body_info": other_body_info,
            "search_info": search_info,
            "feedback": feedback
        }
        logging.info(chat_structure)

        # Generate next conversation action using LLM
        chat_complete_res = self.simple_infer(
            bodydata=str(user_body_data),
            previous_search=str(search_info),
            feedback=str(feedback)
        )
        content = chat_complete_res["choices"][0]["message"].get("content")
        content = self._extract_from_result(content)
        
        # Handle follow-up question flow
        if content.get("conversation"):
            question = content["conversation"]
            #self.callback.send_block(self.workflow_instance_id, msg=question)
            user_input = self.input.read_input(workflow_instance_id=self.workflow_instance_id, input_prompt=question+'\n')
            content = user_input['messages'][-1]['content']
            for content_item in content:
                if content_item['type'] == 'text':
                    answer = content_item['data']
            
            # Store Q&A exchange in conversation history
            user_body_data.append("Question: "+question+"\n"+"Answer: "+answer)
            
            self.stm(self.workflow_instance_id)["user_body_data"] = user_body_data
            return 
        
        # Handle web search flow for gathering contextual info
        elif content.get("tool_call"):
            self.callback.info(self.workflow_instance_id, progress='Body analysis QA', message='Search for information')
            print('----------------------------------------')
            print(content["tool_call"])
            execution_status, execution_results = self.tool_manager.execute_task(
                content["tool_call"]+'\nYou should use web search to complete this task.'
            )
            if execution_status == "success":
                search_info.append(str(execution_results))
                self.stm(self.workflow_instance_id)["search_info"] = search_info
                feedback.append(f'The information of \'{content["tool_call"]}\' is provided detailly and specifically, and satisfied the requirement, dont need to ask for more information.')
                self.stm(self.workflow_instance_id)["feedback"] = feedback
                return
            else:
                raise ValueError("Web search tool execution failed.")

        else:
            raise ValueError("LLM generation is not valid.")


    def _extract_from_result(self, result: str) -> dict:
        try:
            pattern = r"```json\s+(.*?)\s+```"
            match = re.search(pattern, result, re.DOTALL)
            if match:
                return json_repair.loads(match.group(1))
            else:
                return json_repair.loads(result)
        except Exception as error:
            raise ValueError("LLM generation is not valid.")