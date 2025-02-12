# Import required modules and components
import os
from pathlib import Path

from omagent_core.clients.devices.cli import DefaultClient

from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.utils.container import container
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry

# This is a demo for image chat, show how to chat with image by LLM
# Initialize logging
logging.init_logger("omagent", "omagent", level="INFO")

# Set current working directory path
CURRENT_PATH = Path(__file__).parents[0]

# Import registered modules
registry.import_module(project_path=CURRENT_PATH.joinpath("agent"))

container.register_stm("RedisSTM")
# Load container configuration from YAML file
container.from_config(CURRENT_PATH.joinpath("container.yaml"))

# Initialize image chat demo workflow
workflow = ConductorWorkflow(name="image_chat_demo")

# Configure workflow tasks:
# 2. Image chat processing based on user input
task1 = simple_task(
    task_def_name="ImageChat",
    task_reference_name="image_chat",
    inputs={
        "image_url": "https://media.githubusercontent.com/media/om-ai-lab/OmAgent/refs/heads/main/docs/images/intro.png"
    },
)

# Configure workflow execution flow: Input -> Image chat
workflow >> task1

# Register workflow
workflow.register(True)

# Initialize and start CLI client with workflow configuration
config_path = CURRENT_PATH.joinpath("configs")
cli_client = DefaultClient(interactor=workflow, config_path=config_path, workers=[])
cli_client.start_interactor()
