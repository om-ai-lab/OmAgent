# Import core dependencies
import os
os.environ["OMAGENT_MODE"] = "lite"

from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.utils.container import container
from omagent_core.utils.logger import logging

logging.init_logger("omagent", "omagent", level="INFO")

# Set up file paths
from pathlib import Path

CURRENT_PATH = Path(__file__).parents[0]

# Import and initialize registry
from omagent_core.utils.registry import registry

registry.import_module(project_path=CURRENT_PATH.joinpath("agent"))

from omagent_core.clients.devices.app.image_index import ImageIndexListener
# Import client components
from omagent_core.clients.devices.cli import DefaultClient

# Configure storage systems
container.register_stm("SharedMemSTM")
container.register_ltm("MilvusLTM")
container.from_config(CURRENT_PATH.joinpath("container.yaml"))

# Create image storage workflow
workflow = ConductorWorkflow(name="step4_image_storage")

# Define workflow tasks:
# 1. Listen for and detect new images
task1 = simple_task(
    task_def_name="ImageIndexListener", task_reference_name="image_index_listener"
)
# 2. Process and prepare images for storage
task2 = simple_task(
    task_def_name="OutfitImagePreprocessor",
    task_reference_name="outfit_image_preprocessor",
    inputs={"image_data": task1.output("output")},
)

# Set up task sequence
workflow >> task1 >> task2

# Register the workflow with Conductor
workflow.register(True)

# Start CLI client with workflow and image listener
config_path = CURRENT_PATH.joinpath("configs")
agent_client = DefaultClient(
    processor=workflow, config_path=config_path, workers=[ImageIndexListener()]
)
agent_client.start_processor()
