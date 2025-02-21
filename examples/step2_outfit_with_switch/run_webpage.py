# Import required modules from omagent_core
import os
os.environ["OMAGENT_MODE"] = "lite"

from omagent_core.clients.devices.webpage import \
    WebpageClient  # For webpage client interface
from omagent_core.engine.workflow.conductor_workflow import \
    ConductorWorkflow  # For workflow management
from omagent_core.engine.workflow.task.simple_task import \
    simple_task  # For defining workflow tasks
from omagent_core.utils.container import \
    container  # For dependency injection container
from omagent_core.utils.logger import logging  # For logging functionality
from omagent_core.utils.registry import registry  # For registering components

logging.init_logger("omagent", "omagent", level="INFO")  # Initialize logger

# Set up path configuration
from pathlib import Path

CURRENT_PATH = Path(__file__).parents[0]  # Get current directory path
# Import agent modules
registry.import_module(project_path=CURRENT_PATH.joinpath("agent"))

# Add parent directory to Python path for imports
import sys

sys.path.append(os.path.abspath(CURRENT_PATH.joinpath("../../")))

# Import input interface from previous example
from examples.step1_simpleVQA.agent.input_interface.input_interface import \
    InputInterface

# Load container configuration from YAML file
# This configures dependencies like Redis connections and API endpoints
container.register_stm("RedisSTM")
container.from_config(CURRENT_PATH.joinpath("container.yaml"))


# Initialize outfit recommendation workflow with unique name
# This workflow will handle the outfit recommendation process
workflow = ConductorWorkflow(name="step2_outfit_with_switch")

# Configure workflow tasks:
# 1. Input interface task to get user's clothing request
task1 = simple_task(task_def_name="InputInterface", task_reference_name="input_task")
# 2. Weather decision task to determine if weather info is needed
task2 = simple_task(
    task_def_name="WeatherDecider",
    task_reference_name="weather_decider",
    inputs={"user_instruction": task1.output("user_instruction")},
)
# 3. Weather search task to fetch current weather conditions if needed
task3 = simple_task(
    task_def_name="WeatherSearcher",
    task_reference_name="weather_searcher",
    inputs={"user_instruction": task1.output("user_instruction")},
)
# 4. Outfit recommendation task to generate final clothing suggestions
task4 = simple_task(
    task_def_name="OutfitRecommendation", task_reference_name="outfit_recommendation"
)

# Configure workflow execution flow:
# The workflow follows this sequence:
# 1. Get user input
# 2. Analyze if weather info is needed
# 3. Conditionally fetch weather (only if decision task returns 0)
# 4. Generate outfit recommendations based on all gathered info
workflow >> task1 >> task2 >> {0: task3} >> task4

# Register workflow
workflow.register(True)

# Initialize and start app client with workflow configuration
config_path = CURRENT_PATH.joinpath("configs")
agent_client = WebpageClient(
    interactor=workflow, config_path=config_path, workers=[InputInterface()]
)
agent_client.start_interactor()
