from examples.step1_simpleVQA.agent.input_interface.input_interface import InputIterface
from examples.step1_simpleVQA.agent.simple_vqa.simple_vqa import SimpleVQA

# Import required modules and components
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from pathlib import Path
from omagent_core.clients.devices.cli.client import DefaultClient
from omagent_core.utils.logger import logging

import sys
import os
from pathlib import Path
CURRENT_PATH = Path(__file__).parents[0]
sys.path.append(os.path.abspath(CURRENT_PATH.joinpath('../../')))


logging.init_logger("omagent", "omagent", level="INFO")

workflow = ConductorWorkflow(name='example1')
task1 = simple_task(task_def_name='InputIterface', task_reference_name='input_task')
task2 = simple_task(task_def_name='SimpleVQA', task_reference_name='simple_vqa', inputs={'user_instruction': task1.output('user_instruction')})
workflow >> task1 >> task2

# Register workflow
workflow.register(True)

agent_client = DefaultClient(interactor=workflow, config_path='examples/step1_simpleVQA/configs', workers=[InputIterface()])
agent_client.start_interactor()