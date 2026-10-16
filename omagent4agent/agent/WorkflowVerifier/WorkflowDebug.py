from pathlib import Path
from typing import List


from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.base import BaseLLMBackend, BaseLLM
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.utils.registry import registry
from pydantic import Field
from omagent_core.models.llms.prompt.parser import *    
CURRENT_PATH = root_path = Path(__file__).parents[0]


@registry.register_worker()
class WorkflowDebug(BaseLLMBackend, BaseWorker):
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(CURRENT_PATH.joinpath("workflow_debug_system.prompt"), role="system"),
            PromptTemplate.from_file(CURRENT_PATH.joinpath("workflow_debug_user.prompt"), role="user"),   
        ]
    )
    llm: BaseLLM
    def _run(self, *args, **kwargs):        
        initial_description = self.stm(self.workflow_instance_id)["initial_description"]
        example_input = self.stm(self.workflow_instance_id)["example_input"]
        if type(example_input) == str:
            print (example_input)
            example_input = json.loads(example_input)
        workflow_json = self.stm(self.workflow_instance_id)["workflow_json"]       
        workflow_error_msg = self.stm(self.workflow_instance_id)["workflow_error_msg"]
        plan = self.stm(self.workflow_instance_id)["plan"]       
        keys = example_input.keys()

        workflow_json = self.simple_infer(content=initial_description, plan=plan, input=example_input, input_keys=keys, workflow_json=workflow_json, workflow_error_msg=workflow_error_msg)["choices"][0]["message"].get("content")

        self.callback.info(self.workflow_instance_id, progress="WorkflowManager", message=workflow_json)
        self.stm(self.workflow_instance_id)["workflow_json"] = workflow_json
        return workflow_json

