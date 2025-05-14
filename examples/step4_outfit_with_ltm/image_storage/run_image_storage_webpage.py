# Import required modules and components
import os
os.environ["OMAGENT_MODE"] = "lite"
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.utils.container import container
from omagent_core.utils.logger import logging

logging.init_logger("omagent", "omagent", level="INFO")

# Set up paths and registry
from pathlib import Path

CURRENT_PATH = Path(__file__).parents[0]

from omagent_core.utils.registry import registry

registry.import_module(project_path=CURRENT_PATH.joinpath("agent"))

from omagent_core.clients.devices.app.image_index import ImageIndexListener
# Import app-specific components
from omagent_core.clients.devices.webpage import WebpageClient

# Configure container with storage systems
container.register_stm(stm="RedisSTM")
container.register_ltm(ltm="MilvusLTM")
container.from_config(CURRENT_PATH.joinpath("container.yaml"))

# Initialize image storage workflow
workflow = ConductorWorkflow(name="step4_image_storage")

# Configure workflow tasks:
# 1. Listen for new images
task1 = simple_task(
    task_def_name="ImageIndexListener", task_reference_name="image_index_listener"
)

# 2. Preprocess images for storage
task2 = simple_task(
    task_def_name="OutfitImagePreprocessor",
    task_reference_name="outfit_image_preprocessor",
    inputs={"image_data": task1.output("output")},
)

# Configure workflow execution flow: Listen -> Preprocess
workflow >> task1 >> task2

# Register workflow
workflow.register(True)

# Initialize and start app client with workflow configuration
config_path = CURRENT_PATH.joinpath("configs")
agent_client = WebpageClient(
    processor=workflow, config_path=config_path, workers=[ImageIndexListener()]
)
agent_client.start_processor()
