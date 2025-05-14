# Import required modules and components
from pathlib import Path

from omagent_core.clients.devices.app.client import AppClient
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.utils.container import container
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry

logging.init_logger("omagent", "omagent", level="INFO")

# Import agent-specific components
from agent.input_interface.input_interface import InputInterface

# Set current working directory path
CURRENT_PATH = root_path = Path(__file__).parents[0]

# Import registered modules
registry.import_module(project_path=CURRENT_PATH.joinpath("agent"))

container.register_stm("SharedMemSTM")
# Load container configuration from YAML file
container.from_config(CURRENT_PATH.joinpath("container.yaml"))


# Initialize simple VQA workflow
workflow = ConductorWorkflow(name="step1_simpleVQA")

# Configure workflow tasks:
# 1. Input interface for user interaction
task1 = simple_task(task_def_name="InputInterface", task_reference_name="input_task")
# 2. Simple VQA processing based on user input
task2 = simple_task(
    task_def_name="SimpleVQA",
    task_reference_name="simple_vqa",
    inputs={"user_instruction": task1.output("user_instruction")},
)

# Configure workflow execution flow: Input -> VQA
workflow >> task1 >> task2

# Register workflow
workflow.register(True)

# Initialize and start app client with workflow configuration
config_path = CURRENT_PATH.joinpath("configs")
agent_client = AppClient(
    interactor=workflow, config_path=config_path, workers=[InputInterface()]
)
agent_client.start_interactor()
