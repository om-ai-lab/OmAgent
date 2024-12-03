
# Import required modules and components
from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.cli.client import DefaultClient
from omagent_core.utils.logger import logging
from agent.input_interface.dnc_input_interface import DnCInputIterface

# Initialize logging
logging.init_logger("omagent", "omagent", level="INFO")

# Set current working directory path
CURRENT_PATH = Path(__file__).parents[0]

# Import registered modules
registry.import_module(project_path=CURRENT_PATH.joinpath('agent'))

container.register_stm("RedisSTM")
# Load container configuration from YAML file
container.from_config(CURRENT_PATH.joinpath('container.yaml'))


# Initialize the workflow
workflow = ConductorWorkflow(name="divide_and_conquer_workflow")

# Input task
input_task = simple_task(
    task_def_name="DnCInputIterface",
    task_reference_name="input_task"
)

# DnC generation task
dnc_task = simple_task(
    task_def_name="DnCGeneration",
    task_reference_name="dnc_task",
    inputs={
        "concepts": input_task.output("concepts")
    }
)


# Add tasks to the workflow
workflow >> input_task >> dnc_task

# Register the workflow
workflow.register(overwrite=True)

# Initialize and start app client with workflow configuration
config_path = CURRENT_PATH.joinpath('configs')

cli_client = DefaultClient(interactor=workflow, config_path=config_path, workers=[DnCInputIterface()])
cli_client.start_interactor()
