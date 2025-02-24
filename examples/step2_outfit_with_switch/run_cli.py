import os
os.environ["OMAGENT_MODE"] = "lite"
# Import required modules from omagent_core
from omagent_core.clients.devices.cli import \
    DefaultClient  # For CLI client interface
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

import os
# Add parent directory to Python path for imports
import sys

sys.path.append(os.path.abspath(CURRENT_PATH.joinpath("../../")))
# Import input interface from previous example
from examples.step1_simpleVQA.agent.input_interface.input_interface import \
    InputInterface

# Load container configuration from YAML file
# This configures dependencies like Redis connections and API endpoints
container.register_stm("SharedMemSTM")
container.from_config(CURRENT_PATH.joinpath("container.yaml"))


# Initialize outfit recommendation workflow with unique name
# This workflow will handle the outfit recommendation process
workflow = ConductorWorkflow(name="step2_outfit_with_switch")

# Configure workflow tasks:
# 1. Input interface for user interaction
task1 = simple_task(task_def_name="InputInterface", task_reference_name="input_task")
# 2. Weather decision logic based on user input
task2 = simple_task(
    task_def_name="WeatherDecider",
    task_reference_name="weather_decider",
    inputs={"user_instruction": task1.output("user_instruction")},
)
# 3. Weather information retrieval
task3 = simple_task(
    task_def_name="WeatherSearcher",
    task_reference_name="weather_searcher",
    inputs={"user_instruction": task1.output("user_instruction")},
)
# 4. Final outfit recommendation generation
task4 = simple_task(
    task_def_name="OutfitRecommendation", task_reference_name="outfit_recommendation"
)

# Configure workflow execution flow:
# Input -> Weather Decision -> Optional Weather Search -> Outfit Recommendation
# Weather search is only executed if weather information is needed (condition = 0)
workflow >> task1 >> task2 >> {0: task3} >> task4

# Register workflow
workflow.register(True)

# Initialize and start CLI client with workflow configuration
config_path = CURRENT_PATH.joinpath("configs")
cli_client = DefaultClient(
    interactor=workflow, config_path=config_path, workers=[InputInterface()]
)
cli_client.start_interactor()
