from pathlib import Path
from typing import List
import json
import os

from omagent_core.advanced_components.workflow.dnc.schemas.dnc_structure import \
    TaskTree
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
from pprint import pprint

try:
    from omagent_core.clients.devices.utils.workflow_visualizer import visualize_workflow_graph
except ImportError:
    # Create a fallback function if the visualizer is not available
    def visualize_workflow_graph(workflow_json):
        return None

CURRENT_PATH = root_path = Path(__file__).parents[0]


@registry.register_worker()
class WorkflowManager(BaseLLMBackend, BaseWorker):
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(CURRENT_PATH.joinpath("workflow_manager_system.prompt"), role="system"),
            PromptTemplate.from_file(CURRENT_PATH.joinpath("workflow_manager_user.prompt"), role="user"),   
        ]
    )
    llm: BaseLLM
    def _run(self, *args, **kwargs):        
        initial_description = self.stm(self.workflow_instance_id)["initial_description"]
        example_input = self.stm(self.workflow_instance_id)["example_input"]
        if type(example_input) == str:            
            example_input = example_input.replace('"','"').replace('"','"')
            example_input = json.loads(example_input)

        keys = example_input.keys()
        input_parameters = {}
        for k in keys:
            input_parameters[k] = "${workflow.input."+k+"}"

        plan = self.stm(self.workflow_instance_id)["plan"]       
        print (json.dumps({"inputParameters":input_parameters}))
        workflow_json = self.simple_infer(content=initial_description, plan=plan, input=json.dumps({"inputParameters":input_parameters}))["choices"][0]["message"].get("content")
        workflow_json = self.parse(workflow_json)

        workflow = json.loads(workflow_json)
        self.callback.info(self.workflow_instance_id, progress="Workflow", message=json.dumps({"tasks":workflow["tasks"],"name":workflow["name"]}, indent=2))
        
        # Add graph visualization
        try:
            workflow_img = visualize_workflow_graph(workflow_json)
            if workflow_img:
                self.callback.info_image(self.workflow_instance_id, progress="Workflow Graph", image=workflow_img)
        except Exception as e:
            self.callback.info(self.workflow_instance_id, progress="Workflow Graph Error", message=f"Error creating workflow visualization: {str(e)}")
        
        self.stm(self.workflow_instance_id)["workflow_json"] = workflow_json
        self.callback.info(self.workflow_instance_id, progress="Reasoning...", message=workflow["reasoning"])
        return workflow_json

    def parse(self, workflow_json):
        workflow_json = workflow_json.replace('```json', '').replace('```', '')
        workflow_json = workflow_json.strip()
        return workflow_json