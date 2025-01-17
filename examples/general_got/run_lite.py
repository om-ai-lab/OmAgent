# Import required modules and components
import os
from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from pathlib import Path
from omagent_core.utils.registry import registry
#from omagent_core.clients.devices.cli.client import DefaultClient
from omagent_core.clients.devices.lite_version.cli import DefaultClient
from omagent_core.utils.logger import logging

from omagent_core.engine.worker.base import BaseWorker
from colorama import Fore
import json

from agent.input_interface.input_interface import InputInterfaceGot
# from omagent_core.advanced_components.workflow.dnc.workflow import DnCWorkflow
from omagent_core.advanced_components.workflow.general_got.workflow import GoTWorkflow

@registry.register_worker()
class SimpleInput(BaseWorker):
    def _run(self, query, *args, **kwargs):
        return {"query":"[6, 3, 6, 5, 1, 2, 4, 3, 8, 0, 7, 8, 6, 4, 9, 5, 2, 4, 8, 4, 4, 4, 5, 6, 8, 4, 7, 7, 8, 9, 4, 9]", "task":"sort", "meta":None}
    


# Initialize logging
logging.init_logger("omagent", "omagent", level="INFO")

# Set current working directory path
CURRENT_PATH = Path(__file__).parents[0]

# Import registered modules
registry.import_module(project_path=CURRENT_PATH.joinpath('agent'))

container.register_stm("SharedMemSTM")
# Load container configuration from YAML file
#container.from_config(CURRENT_PATH.joinpath('container.yaml'))



# Initialize Got workflow
workflow = ConductorWorkflow(name='GoT', lite_version=True)

# Configure workflow tasks:
client_input_task = simple_task(task_def_name=SimpleInput, task_reference_name='input_task' )

got_workflow = GoTWorkflow()
got_workflow.set_input(query=client_input_task.output('query'), task=client_input_task.output('task'), meta=client_input_task.output('meta'))
workflow >> client_input_task >> got_workflow

# Register workflow
workflow.register(True)

# Initialize and start CLI client with workflow configuration
config_path = CURRENT_PATH.joinpath('configs')
cli_client = DefaultClient(interactor=workflow, config_path=config_path, workers=[SimpleInput()])
# cli_client.start_interaction()
cli_client.start_processor_with_input({"query":"[6, 3, 6, 5, 1, 2, 4, 3, 8, 0, 7, 8, 6, 4, 9, 5, 2, 4, 8, 4, 4, 4, 5, 6, 8, 4, 7, 7, 8, 9, 4, 9]", "task":"sort", "meta":None})

