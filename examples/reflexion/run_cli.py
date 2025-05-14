from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.cli import DefaultClient
from omagent_core.utils.logger import logging
from omagent_core.advanced_components.workflow.reflexion.workflow import ReflexionWorkflow
from agent.input_interface.input_interface import InputInterface


logging.init_logger("omagent", "omagent", level="INFO")

# Set current working directory path
CURRENT_PATH = Path(__file__).parents[0]

# Import registered modules
registry.import_module(CURRENT_PATH.joinpath('agent'))

# Load container configuration from YAML file
container.register_stm("SharedMemSTM")
container.from_config(CURRENT_PATH.joinpath('container.yaml'))

# Initialize workflow
workflow = ConductorWorkflow(name='reflexion')

# Configure input task
input_task = simple_task(
    task_def_name=InputInterface,
    task_reference_name='input_interface'
)

# Configure React Pro Reflexion workflow
reflexion_workflow = ReflexionWorkflow()
reflexion_workflow.set_input(
    query=input_task.output('query')
)

# Configure workflow execution flow
workflow >> input_task >> reflexion_workflow

# Register workflow
workflow.register(overwrite=True)

# Initialize and start CLI client
config_path = CURRENT_PATH.joinpath('configs')
cli_client = DefaultClient(
    interactor=workflow, config_path=config_path, workers=[]
)

cli_client.start_interactor()
