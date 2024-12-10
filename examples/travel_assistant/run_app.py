# Import required modules from omagent_core
from omagent_core.utils.container import container  # For dependency injection container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow  # For workflow management
from omagent_core.engine.workflow.task.simple_task import simple_task  # For defining workflow tasks
from omagent_core.utils.registry import registry  # For registering components
from omagent_core.clients.devices.app.client import AppClient  # For app client interface
from omagent_core.utils.logger import logging  # For logging functionality
logging.init_logger("omagent", "omagent", level="INFO")  # Initialize logger

# Set up path configuration
from pathlib import Path
CURRENT_PATH = Path(__file__).parents[0]  # Get current directory path
# Import agent modules
registry.import_module(project_path=CURRENT_PATH.joinpath('agent'))

# Add parent directory to Python path for imports
import sys
import os
sys.path.append(os.path.abspath(CURRENT_PATH.joinpath('../../')))

# Import input interface from previous example
from examples.step1_simpleVQA.agent.input_interface.input_interface import InputInterface

# Import loop task type for iterative Q&A
from omagent_core.engine.workflow.task.do_while_task import DoWhileTask

# Load container configuration from YAML file
# This configures dependencies like Redis connections and API endpoints
container.register_stm("RedisSTM")
container.from_config(CURRENT_PATH.joinpath('container.yaml'))


# Initialize scenic spot recommendation workflow with unique name
# This workflow will handle the scenic spot recommendation process
workflow = ConductorWorkflow(name='traval_assistant')

# Configure workflow tasks:

# task1:
#   task_def_name='ScenicSpotQA': Task for Scenic Spot Q&A, involves asking questions about scenic spots and gathering information.
#   task_reference_name='scenic_spot_qa': Reference name for the task, uniquely identifies and references this task in the workflow.

# task2:
#   task_def_name='ScenicSpotDecider': Task for Scenic Spot Decider, makes decisions based on user preferences and Q&A information.
#   task_reference_name='scenic_spot_decider': Reference name for the task, uniquely identifies and references this task in the workflow.

# task3:
#   task_def_name='ScenicSpotRecommendation': Task for generating final scenic spot recommendations based on user preferences and decisions.
#   task_reference_name='scenic_spot_recommendation': Reference name for the task, uniquely identifies and references this task in the workflow.


task1 = simple_task(task_def_name='ScenicSpotQA', task_reference_name='scenic_spot_qa')

task2 = simple_task(task_def_name='ScenicSpotDecider', task_reference_name='scenic_spot_decider')

task3 = simple_task(task_def_name='ScenicSpotRecommendation', task_reference_name='scenic_spot_recommendation')

# Create loop that continues Q&A until sufficient information is gathered
# Loop terminates when scenic_spot_decider returns decision=true
scenic_spot_qa_loop = DoWhileTask(task_ref_name='preference_loop', tasks=[task1, task2], 
                             termination_condition='if ($.scenic_spot_decider["decision"] == true){false;} else {true;} ')

# Configure workflow execution flow:
workflow >> scenic_spot_qa_loop >> task3

# Register workflow
workflow.register(True)

# Initialize and start app client with workflow configuration
config_path = CURRENT_PATH.joinpath('configs')
agent_client = AppClient(interactor=workflow, config_path=config_path)
agent_client.start_interactor()
