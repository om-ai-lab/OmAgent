# Import core OmAgent components for workflow management and app functionality
from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.clients.devices.app.client import AppClient
from omagent_core.utils.logger import logging
logging.init_logger("omagent", "omagent", level="INFO")

from omagent_core.utils.registry import registry

from pathlib import Path
CURRENT_PATH = Path(__file__).parents[0]

# Import and register worker modules from agent directory
registry.import_module(project_path=CURRENT_PATH.joinpath('agent'))

# Add parent directory to Python path for imports
import sys
import os
sys.path.append(os.path.abspath(CURRENT_PATH.joinpath('../../')))

# Import custom image input worker

# Import task type for implementing loops in workflow
from omagent_core.engine.workflow.task.do_while_task import DoWhileTask
from agent.input_interface.input_interface import InputInterface

# Configure container with Redis storage and load settings
container.register_stm("RedisSTM")
container.from_config(CURRENT_PATH.joinpath('container.yaml'))


# Initialize outfit recommendation workflow
workflow = ConductorWorkflow(name='Guessing_Game')

# Define workflow tasks:
task1 = simple_task(task_def_name='InputInterface', task_reference_name='input_task')

# 1. Ask questions about the outfit
task2 = simple_task(task_def_name='GuessingGameQA', task_reference_name='guessing_game_qa')

# 2. Check if enough information is gathered
task3 = simple_task(task_def_name='GuessingGameDecider', task_reference_name='guessing_game_decider')

# 3. Generate final outfit recommendations
task4 = simple_task(task_def_name='GuessingGameResult', task_reference_name='guessing_game_result')

# Create loop that continues Q&A until sufficient information is gathered
# Loop terminates when outfit_decider returns decision=true
guessing_game_qa_loop = DoWhileTask(task_ref_name='guessing_game_qa_loop', tasks=[task2, task3], 
                             termination_condition='if ($.guessing_game_decider["decision"] == true){false;} else {true;} ')

# Define workflow sequence: image input -> Q&A loop -> final recommendation
workflow >> guessing_game_qa_loop >> task4

# Register workflow with conductor server
workflow.register(True)

# Initialize and start app client with workflow and image input worker
config_path = CURRENT_PATH.joinpath('configs')
agent_client = AppClient(interactor=workflow, config_path=config_path, workers=[InputInterface()])
agent_client.start_interactor()
