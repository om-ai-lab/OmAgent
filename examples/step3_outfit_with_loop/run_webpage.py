# Import core OmAgent components for workflow management and app functionality
import os
os.environ["OMAGENT_MODE"] = "lite"
from omagent_core.clients.devices.webpage import WebpageClient
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.utils.container import container
from omagent_core.utils.logger import logging

logging.init_logger("omagent", "omagent", level="INFO")

from pathlib import Path

from omagent_core.utils.registry import registry

CURRENT_PATH = Path(__file__).parents[0]

# Import and register worker modules from agent directory
registry.import_module(project_path=CURRENT_PATH.joinpath("agent"))

# Add parent directory to Python path for imports
import sys

sys.path.append(os.path.abspath(CURRENT_PATH.joinpath("../../")))

# Import custom image input worker
from agent.outfit_image_input.outfit_image_input import OutfitImageInput
# Import task type for implementing loops in workflow
from omagent_core.engine.workflow.task.do_while_task import DoWhileTask

from examples.step2_outfit_with_switch.agent.outfit_recommendation.outfit_recommendation import \
    OutfitRecommendation

# Configure container with Redis storage and load settings
container.register_stm("RedisSTM")
container.from_config(CURRENT_PATH.joinpath("container.yaml"))


# Initialize workflow for outfit recommendations with loops
workflow = ConductorWorkflow(name="step3_outfit_with_loop")

# Define workflow tasks:
# 1. Get initial outfit image input
task1 = simple_task(task_def_name="OutfitImageInput", task_reference_name="image_input")

# 2. Ask questions about the outfit
task2 = simple_task(task_def_name="OutfitQA", task_reference_name="outfit_qa")

# 3. Decide if enough information is gathered
task3 = simple_task(task_def_name="OutfitDecider", task_reference_name="outfit_decider")

# 4. Generate final outfit recommendations
task4 = simple_task(
    task_def_name="OutfitRecommendation", task_reference_name="outfit_recommendation"
)

# Create loop that continues Q&A until sufficient information is gathered
# Loop terminates when outfit_decider returns decision=true
outfit_qa_loop = DoWhileTask(
    task_ref_name="outfit_loop",
    tasks=[task2, task3],
    termination_condition='if ($.outfit_decider["decision"] == true){false;} else {true;} ',
)

# Define workflow sequence: image input -> Q&A loop -> final recommendation
workflow >> task1 >> outfit_qa_loop >> task4

# Register workflow with conductor server
workflow.register(True)

# Initialize and start app client with workflow and image input worker
config_path = CURRENT_PATH.joinpath("configs")
agent_client = WebpageClient(
    interactor=workflow, config_path=config_path, workers=[OutfitImageInput()]
)
agent_client.start_interactor()
