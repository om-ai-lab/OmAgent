from omagent_core.advanced_components.workflow.dnc.workflow import DnCWorkflow
from omagent_core.utils.container import container
from agent.input_interface.input_interface import InputInterface
from agent.conclude.conclude import Conclude

from pathlib import Path
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
from omagent_core.engine.workflow.task.simple_task import simple_task

from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.clients.devices.cli.lite_client import LiteClient

logging.init_logger("omagent", "omagent", level="INFO")
# Set current working directory path
CURRENT_PATH = root_path = Path(__file__).parents[0]

# Import registered modules
registry.import_module(CURRENT_PATH.joinpath('agent'))

# Register memory storage    
container.register_stm("SharedMemSTM")
workflow = ConductorWorkflow(name='general_dnc', lite_version=True)

client_input_task = simple_task(task_def_name=InputInterface, task_reference_name='input_interface')

dnc_workflow = DnCWorkflow()


dnc_workflow.set_input(query=client_input_task.output('query'))


conclude_task = simple_task(task_def_name=Conclude, task_reference_name='task_conclude', inputs={'dnc_structure': dnc_workflow.dnc_structure, 'last_output': dnc_workflow.last_output})


# Configure workflow execution flow: Input -> Initialize global variables -> DnC Loop -> Conclude
workflow >> client_input_task >> dnc_workflow >> conclude_task

workflow.register(overwrite=True)
config_path = CURRENT_PATH.joinpath('configs')

cli_client = LiteClient(config_path=config_path, workflow=workflow)
cli_client.start_interactor()
