# Import core modules and components for the Program of Thought (PoT) workflow
import os
os.environ["OMAGENT_MODE"] = "lite"

from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from agent.input_interface.input_interface import PoTInputInterface
from omagent_core.advanced_components.workflow.pot.workflow import PoTWorkflow
from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.cli import DefaultClient

from omagent_core.utils.logger import logging


# Initialize logging with INFO level
logging.init_logger("omagent", "omagent", level="INFO")

# Get the root directory path
CURRENT_PATH = Path(__file__).parents[0]

# Load custom agent modules from the project directory
registry.import_module(project_path=CURRENT_PATH.joinpath('agent'))

# Load container configuration from YAML file
container.from_config(CURRENT_PATH.joinpath('container.yaml'))


# Initialize the main Program of Thought workflow
workflow = ConductorWorkflow(name='PoT')

# Create input interface task to handle user interactions
client_input_task = simple_task(task_def_name=PoTInputInterface, task_reference_name='PoT_input_interface')

# Initialize PoT workflow and connect it with input task outputs
pot_workflow = PoTWorkflow()
pot_workflow.set_input(query=client_input_task.output('query'), examples=client_input_task.output('examples'), options=client_input_task.output('options'))

# Chain tasks together: Input Interface -> PoT Workflow
workflow >> client_input_task >> pot_workflow

# Register workflow with overwrite option enabled
workflow.register(overwrite=True)

# Initialize and start CLI client with configured workflow
config_path = CURRENT_PATH.joinpath('configs')
cli_client = DefaultClient(interactor=workflow, config_path=config_path, workers=[PoTInputInterface()])
cli_client.start_interactor()
