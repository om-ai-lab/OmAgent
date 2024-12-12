# Import core modules for workflow management and configuration
from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.utils.logger import logging
logging.init_logger("omagent", "omagent", level="INFO")

# Import registry and CLI client modules
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.cli.client import DefaultClient

from pathlib import Path
CURRENT_PATH = Path(__file__).parents[0]

# Import and register worker modules from agent directory
registry.import_module(project_path=CURRENT_PATH.joinpath('agent'))

# Add parent directory to Python path
import sys
import os
sys.path.append(os.path.abspath(CURRENT_PATH.joinpath('../../')))

# Import custom outfit image input worker
from agent.hand_image_input.image_input import HandImageInput
from agent.face_image_input.image_input import FaceImageInput
from agent.text_input.input_interface import InputInterface

# Import loop task type for iterative Q&A
from omagent_core.engine.workflow.task.do_while_task import DoWhileTask


# Configure Redis storage and load container settings
container.register_stm("RedisSTM")
container.from_config(CURRENT_PATH.joinpath('container.yaml'))


# Initialize outfit recommendation workflow
workflow = ConductorWorkflow(name='dangerous_driving_detection')

# Define workflow tasks:
# 1. Get initial hand image from user
task1 = simple_task(task_def_name='HandImageInput', task_reference_name='hand_image_input')

# 2. Get initial face image from user
task2 = simple_task(task_def_name='FaceImageInput', task_reference_name='face_image_input')

# 3. Get initial text input from user
task3 = simple_task(task_def_name='InputInterface', task_reference_name='text_input')

# 4. Check if user is dangerous driver
task4 = simple_task(task_def_name='LoopDecider', task_reference_name='loop_decider')


# Loop terminates when loop_decider returns decision=true
car_qa_loop = DoWhileTask(task_ref_name='car_loop', tasks=[task1, task2, task3, task4], 
                             termination_condition='if ($.loop_decider["decision"] == true){false;} else {true;} ')

# Define workflow sequence: workflow -> car_qa_loop
workflow >> car_qa_loop

# Register workflow with conductor server
workflow.register(True)

# Initialize and start CLI client with workflow and image input worker
config_path = CURRENT_PATH.joinpath('configs')
cli_client = DefaultClient(interactor=workflow, config_path=config_path, workers=[HandImageInput(), FaceImageInput(), InputInterface()])
cli_client.start_interactor()
