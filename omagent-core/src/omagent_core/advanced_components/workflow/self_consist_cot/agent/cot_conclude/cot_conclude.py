from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.models.llms.schemas import Message, Content
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.utils.logger import logging
from pathlib import Path
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from pydantic import Field
from typing import List

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class COTConclusion(BaseLLMBackend, BaseWorker):

    llm: OpenaiGPTLLM

    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("user_prompt.prompt"), role="user"
            ),
        ]
    )

    def _run(self,  final_answer:List[str],question:str, *args, **kwargs):
        reasoning_result = self.simple_infer(final_answer=str(final_answer))
        prompt_tokens = sum(self.stm(self.workflow_instance_id)['prompt_token'])   + reasoning_result["usage"]["prompt_tokens"]
        completion_tokens = sum(self.stm(self.workflow_instance_id)['completion_token']) + reasoning_result["usage"]["completion_tokens"]
        reasoning_result = reasoning_result["choices"][0]["message"]["content"]
        self.stm(self.workflow_instance_id)['final_answer'] = reasoning_result
        self.callback.send_answer(self.workflow_instance_id, msg={'final_answer': reasoning_result,'question': question,"prompt_tokens":prompt_tokens, "completion_tokens": completion_tokens})
        return {'final_answer': reasoning_result,'question': question,'prompt_tokens': prompt_tokens, 'completion_tokens': completion_tokens}