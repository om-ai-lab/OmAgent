# Import required modules and components
import os
from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()  

from omagent_core.utils.registry import registry
from omagent_core.clients.devices.lite_version.cli import DefaultClient
from omagent_core.utils.logger import logging
from omagent_core.advanced_components.workflow.self_consist_cot.workflow import SelfConsistentWorkflow
import yaml
from omagent_core.engine.worker.base import BaseWorker
logging.init_logger("omagent", "omagent", level="INFO")


@registry.register_worker()
class LiteInputInterface(BaseWorker):

    def _run(self, *args, **kwargs):
        question = input("'Please input your question: ")
        return {'user_question': question}

    
# Set current working directory path
CURRENT_PATH = root_path = Path(__file__).parents[0]

# Load num_path configuration
config_path = CURRENT_PATH.joinpath('configs')

with open(config_path.joinpath('path_config.yaml'), 'r') as f:
    path_config = yaml.safe_load(f)

# Import registered modules
registry.import_module(CURRENT_PATH.joinpath('agent'))

# Load container configuration from YAML file
container.register_stm("SharedMemSTM")

# Initialize general_self_consist_cot workflow
workflow = ConductorWorkflow(name='general_self_consist_cot',lite_version=True)

# Configure workflow tasks:
# 1. Input interface for user interaction
client_input_task = simple_task(task_def_name=LiteInputInterface, task_reference_name='input_interface')
self_consist_cot_workflow = SelfConsistentWorkflow()
self_consist_cot_workflow.set_input(user_question=client_input_task.output('user_question'),num_path=path_config['num_path'])

# Configure workflow execution flow
workflow >> client_input_task >> self_consist_cot_workflow

# Register workflow
workflow.register(overwrite=True)

# Initialize and start app client with workflow configuration


cli_client = DefaultClient(interactor=workflow, config_path=config_path, workers=[LiteInputInterface()])
#cli_client.start_processor_with_input({"question":"1+1=?"})
cli_client.start_interactor()