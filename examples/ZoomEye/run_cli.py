# Import essential components from the OMAgent framework
from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.cli import DefaultClient
from omagent_core.utils.logger import logging
from omagent_core.advanced_components.workflow.ZoomEye.workflow import ZoomEyeWorkflow
from dotenv import load_dotenv
from agent.zoomeye_input.zoomeye_input import ZoomEyeInput

# Load environment variables from .env file
load_dotenv()

# Initialize logging with INFO level
logging.init_logger("omagent", "omagent", level="INFO")

# Set current working directory path for resource location
CURRENT_PATH = Path(__file__).parents[0]

# Import registered modules from the agent directory to register custom components
registry.import_module(project_path=CURRENT_PATH.joinpath('agent'))

# Configure the Short-Term Memory system
container.register_stm("SharedMemSTM")
# Load container configuration from YAML file
container.from_config(CURRENT_PATH.joinpath('container.yaml'))

# Initialize ZoomEye workflow with the ConductorWorkflow
workflow = ConductorWorkflow(name='ZoomEye')

# Define the input task to collect query and image from user
zoom_eye_input_task = simple_task(
    task_def_name='ZoomEyeInput',
    task_reference_name='zoom_eye_input'
)

# Initialize the main ZoomEye processing workflow
zoom_eye_workflow = ZoomEyeWorkflow()

# Set inputs for the ZoomEye workflow from the input task outputs
zoom_eye_workflow.set_input(
    query = zoom_eye_input_task.output("query"),
    image_path = zoom_eye_input_task.output("image_path")
)

# Configure workflow execution flow: 
# First collect input, then process with ZoomEye workflow
workflow >> zoom_eye_input_task >> zoom_eye_workflow

# Register workflow in the system (overwrite if it already exists)
workflow.register(overwrite=True)

# Initialize CLI client with the workflow configuration
config_path = CURRENT_PATH.joinpath('configs')
cli_client = DefaultClient(interactor=workflow, config_path=config_path, workers=[])

# Start the CLI client to begin interaction with the user
cli_client.start_interactor()
