# Import required modules and components
from pathlib import Path
from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.advanced_components.workflow.rap import RAPWorkflow
from omagent_core.clients.devices.cli import DefaultClient
from omagent_core.utils.registry import registry
from omagent_core.utils.logger import logging
from agent.conclude.conclude import Conclude
from agent.input_interface.input_interface import InputInterface

import os
os.environ["OMAGENT_MODE"] = "lite"

# Initialize logging
logging.init_logger("omagent", "omagent", level="INFO")

# Set current working directory path
CURRENT_PATH = Path(__file__).parents[0]

# Import registered modules
registry.import_module(CURRENT_PATH.joinpath("agent"))

# Load container configuration and set STM
container.register_stm("SharedMemSTM")

# Initialize RAP workflow with lite_version=True
workflow = ConductorWorkflow(name="rap_workflow", lite_version=True)

# Configure workflow tasks:
# 1. Input interface for user interaction
client_input_task = simple_task(
    task_def_name=InputInterface, 
    task_reference_name="input_interface"
)

# 2. RAP workflow for reasoning
rap_workflow = RAPWorkflow()
rap_workflow.set_input(query=client_input_task.output("query"))

# 3. Conclude task for final answer
conclude_task = simple_task(
    task_def_name=Conclude,
    task_reference_name="task_conclude",
    inputs={
        "final_answer": rap_workflow.final_answer,
    },
)

# Configure workflow execution flow: Input -> RAP -> Conclude
workflow >> client_input_task >> rap_workflow >> conclude_task

# Register workflow with overwrite=True for lite version
workflow.register(overwrite=True)

# Initialize and start CLI client
config_path = CURRENT_PATH.joinpath("configs")
cli_client = DefaultClient(
    interactor=workflow, 
    config_path=config_path, 
    workers=[InputInterface(), Conclude()]
)
cli_client.start_interactor() 