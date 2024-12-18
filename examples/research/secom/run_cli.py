from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.utils.logger import logging
from pathlib import Path

CURRENT_PATH = Path(__file__).parents[0]
logging.init_logger("omagent", "omagent", level="INFO")

# Import registry and CLI client modules
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.cli.client import DefaultClient

# Register worker modules
registry.import_module(project_path=CURRENT_PATH.joinpath('agent'))

# Configure Redis storage and load container settings
container.register_stm("RedisSTM")
container.from_config(CURRENT_PATH.joinpath('container.yaml'))

# Initialize QA workflow
workflow = ConductorWorkflow(name='qa_workflow')

# Define workflow tasks:
# 1. Input interface for user questions
task1 = simple_task(task_def_name='InputInterface', task_reference_name='input_task')

# 2. QA processor for generating answers and segmenting history
task2 = simple_task(task_def_name='SimpleQA', task_reference_name='qa_task', inputs={
    'user_instruction': task1.output('user_instruction')
})

# Define workflow sequence
workflow >> task1 >> task2

# Register workflow with conductor server
workflow.register(True)

# Initialize and start CLI client
config_path = CURRENT_PATH.joinpath('configs')
cli_client = DefaultClient(interactor=workflow, config_path=config_path)
cli_client.start_interactor()
