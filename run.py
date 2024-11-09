from examples.step1_simpleVQA.agent.simple_vqa.simple_vqa import SimpleVQA
from omagent_core.clients.devices.cli.client import DefaultClient
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task

from omagent_core.utils.logger import logging
import sys
import os
from pathlib import Path
CURRENT_PATH = Path(__file__).parents[0]
sys.path.append(os.path.abspath(CURRENT_PATH.joinpath('../../')))


logging.init_logger("omagent", "omagent", level="INFO")

workflow = ConductorWorkflow(name='example1')
task1 = simple_task(task_def_name='SimpleVQA', task_reference_name='simple_vqa')
workflow >> task1

agent_client = DefaultClient(interactor=workflow, config_path='../examples/step1_simpleVQA/configs')
agent_client.start_interactor()