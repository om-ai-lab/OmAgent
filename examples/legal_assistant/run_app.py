# Import required modules and components
from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.app.client import AppClient
from omagent_core.utils.logger import logging
logging.init_logger("omagent", "omagent", level="INFO")

# Import agent-specific components
from agent.input_interface.input_interface import InputInterface 
from omagent_core.engine.workflow.task.do_while_task import DoWhileTask

# Set current working directory path
CURRENT_PATH = root_path = Path(__file__).parents[0]

# Import registered modules
registry.import_module(project_path=CURRENT_PATH.joinpath('agent'))

container.register_stm("RedisSTM")
# Load container configuration from YAML file
container.from_config(CURRENT_PATH.joinpath('container.yaml'))



# Initialize simple VQA workflow
workflow = ConductorWorkflow(name='legal_assistant')

# Configure workflow tasks:
# 1. Input interface for user interaction
task1 = simple_task(task_def_name='InputInterface', task_reference_name='input_task')
# 2. Simple VQA processing based on user input
task2 = simple_task(task_def_name='SimpleVQA', task_reference_name='simple_vqa', inputs={'user_instruction': task1.output('user_instruction')})

# Create conversation loop task
conversation_loop = DoWhileTask(
    task_ref_name='conversation_loop',
    tasks=[task1, task2],
    condition="true"  # Permanent loop, until user exits
)

# Configure workflow execution flow: Input -> VQA
workflow >> conversation_loop

# Register workflow
workflow.register(True)

# Initialize and start app client with workflow configuration
config_path = CURRENT_PATH.joinpath('configs')
agent_client = AppClient(interactor=workflow, config_path=config_path, workers=[InputInterface()])
agent_client.start_interactor()
