# Import required modules and components
import os
from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.app.client import AppClient
from omagent_core.utils.logger import logging
from agent.input_interface.input_interface import InputInterface
from omagent_core.advanced_components.workflow.cot.workflow import CoTWorkflow
logging.init_logger("omagent", "omagent", level="INFO")

# Set current working directory path
CURRENT_PATH = root_path = Path(__file__).parents[0]

# Import registered modules
registry.import_module(CURRENT_PATH.joinpath('agent'))

# Load container configuration from YAML file
container.register_stm("RedisSTM")
container.from_config(CURRENT_PATH.joinpath('container.yaml'))

# Initialize simple VQA workflow
workflow = ConductorWorkflow(name='cot')

# Configure workflow tasks:
# 1. Input interface for user interaction
client_input_task = simple_task(task_def_name=InputInterface, task_reference_name='input_interface')

cot_workflow = CoTWorkflow()
cot_workflow.set_input(query=client_input_task.output('query'), cot_method=client_input_task.output('cot_method'), cot_examples=client_input_task.output('cot_examples'))

workflow >> client_input_task >> cot_workflow

# Register workflow
workflow.register(overwrite=True)

# Initialize and start app client with workflow configuration
config_path = CURRENT_PATH.joinpath('configs')
app_client = AppClient(interactor=workflow, config_path=config_path, workers=[InputInterface()])
app_client.start_interactor()
