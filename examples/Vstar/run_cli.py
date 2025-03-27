# Import necessary components from the OmAgent core
from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.cli import DefaultClient
from omagent_core.utils.logger import logging
from omagent_core.advanced_components.workflow.Vstar.workflow import VstarWorkflow
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Initialize logging for the OmAgent with INFO level
logging.init_logger("omagent", "omagent", level="INFO")

# Set the current working directory path
CURRENT_PATH = Path(__file__).parents[0]

# Import registered modules from the agent directory
registry.import_module(project_path=CURRENT_PATH.joinpath('agent'))

# Register the shared memory state management (STM) for the workflow
container.register_stm("SharedMemSTM")

# Load container configuration from a YAML file
container.from_config(CURRENT_PATH.joinpath('container.yaml'))

# Initialize a simple VQA (Visual Question Answering) workflow
workflow = ConductorWorkflow(name='Vstar')

# Configure workflow tasks:
# 1. Create an input task for user input
vstar_input_task = simple_task(task_def_name='VstarInput', task_reference_name='vstar_input_task')

# Initialize the Vstar workflow
vstar_workflow = VstarWorkflow()

# Set the input for the Vstar workflow using outputs from the input task
vstar_workflow.set_input(
    query=vstar_input_task.output("query"),
    image_path=vstar_input_task.output("image_path")
)

# Configure the execution flow of the workflow: Input -> Vstar Input Task -> Vstar Workflow
workflow >> vstar_input_task >> vstar_workflow

# Register the workflow with the option to overwrite any existing workflow with the same name
workflow.register(overwrite=True)

# Initialize and start the CLI client with the configured workflow
config_path = CURRENT_PATH.joinpath('configs')
cli_client = DefaultClient(interactor=workflow, config_path=config_path, workers=[])

# Start the interactor for the CLI client
cli_client.start_interactor()
