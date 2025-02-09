from pathlib import Path
from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.cli.client import DefaultClient
from omagent_core.advanced_components.workflow.reflexion import ReflexionWorkflow

# Initialize logging
logging.init_logger("omagent", "omagent", level="INFO")

# Set current working directory path
CURRENT_PATH = Path(__file__).parents[0]

# Import registered modules
registry.import_module(CURRENT_PATH.joinpath("agent"))

# Load container configuration
container.register_stm("RedisSTM")
container.from_config(CURRENT_PATH.joinpath("container.yaml"))

# Initialize workflow
workflow = ConductorWorkflow(name="reflexion_workflow")

# Configure Reflexion workflow
reflexion_workflow = ReflexionWorkflow()
reflexion_workflow.set_input(
    query=workflow.input('query'),
    previous_attempts=workflow.input('previous_attempts'),
    id=workflow.input('id')
)

# Configure workflow execution flow
workflow >> reflexion_workflow

# Register workflow
workflow.register(overwrite=True)

# Initialize and start CLI client
config_path = CURRENT_PATH.joinpath("configs")
cli_client = DefaultClient(
    interactor=workflow,
    config_path=config_path,
    workers=[]
)
cli_client.start_interactor()