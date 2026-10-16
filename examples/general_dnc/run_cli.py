# Import required modules and components
import os
os.environ["OMAGENT_MODE"] = "lite"
from pathlib import Path

from agent.conclude.conclude import Conclude
from agent.input_interface.input_interface import InputInterface
from omagent_core.advanced_components.workflow.dnc.workflow import DnCWorkflow
from omagent_core.clients.devices.cli import DefaultClient
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.utils.container import container
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry

logging.init_logger("omagent", "omagent", level="INFO")

# Set current working directory path
CURRENT_PATH = root_path = Path(__file__).parents[0]

# Import registered modules
registry.import_module(CURRENT_PATH.joinpath("agent"))

# Load container configuration from YAML file
container.register_stm("SharedMemSTM")
container.from_config(CURRENT_PATH.joinpath("container.yaml"))

# Initialize general dnc workflow
workflow = ConductorWorkflow(name="general_dnc")

# Configure workflow tasks:
# 1. Input interface for user interaction
client_input_task = simple_task(
    task_def_name=InputInterface, task_reference_name="input_interface"
)

# 2. DnC workflow for task execution
dnc_workflow = DnCWorkflow()
dnc_workflow.set_input(query=client_input_task.output("query"))

# 3. Conclude task for task conclusion
conclude_task = simple_task(
    task_def_name=Conclude,
    task_reference_name="task_conclude",
    inputs={
        "dnc_structure": dnc_workflow.dnc_structure,
        "last_output": dnc_workflow.last_output,
    },
)


# Configure workflow execution flow: Input -> DnC Loop -> Conclude
workflow >> client_input_task >> dnc_workflow >> conclude_task

# Register workflow
workflow.register(overwrite=True)

# Initialize and start app client with workflow configuration
config_path = CURRENT_PATH.joinpath("configs")
cli_client = DefaultClient(
    interactor=workflow, config_path=config_path, workers=[InputInterface()]
)
cli_client.start_interactor()
