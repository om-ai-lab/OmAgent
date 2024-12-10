# Import required modules and components
from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.engine.workflow.task.do_while_task import DoWhileTask
from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.cli.client import DefaultClient
from omagent_core.utils.logger import logging

from agent.input_interface.input_interface import InputInterface

# Initialize logging
logging.init_logger("omagent", "omagent", level="INFO")

# Set current working directory path
CURRENT_PATH = Path(__file__).parents[0]

# Import registered modules
registry.import_module(project_path=CURRENT_PATH.joinpath('agent'))

container.register_stm("RedisSTM")
# Load container configuration from YAML file
container.from_config(CURRENT_PATH.joinpath('container.yaml'))

# Initialize workflow
workflow = ConductorWorkflow(name='legal_assistant')

# Configure tasks
input_task = simple_task(task_def_name='InputInterface', task_reference_name='input_task')
vqa_task = simple_task(
    task_def_name='LegalAssistant',
    task_reference_name='legal_assistant',
    inputs={'user_instruction': input_task.output('user_instruction')}
)

# Create conversation loop task
conversation_loop = DoWhileTask(
    task_ref_name='conversation_loop',
    tasks=[input_task, vqa_task],
    termination_condition="true"  # Infinite loop until user exits
)

# Configure workflow execution flow
workflow >> conversation_loop

# Register workflow
workflow.register(True)

# Initialize and start CLI client
config_path = CURRENT_PATH.joinpath('configs')
cli_client = DefaultClient(
    interactor=workflow, 
    config_path=config_path, 
    workers=[InputInterface()]
)
cli_client.start_interactor()
