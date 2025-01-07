# Import required modules and components
from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.cli.client import DefaultClient
from omagent_core.engine.workflow.task.set_variable_task import SetVariableTask
from omagent_core.utils.logger import logging
from omagent_core.engine.workflow.task.do_while_task import DoWhileTask

from agent.input_interface.input_interface import InputInterface
from agent.thought_generator.thought_generator import ThoughtGenerator
# Initialize logging
logging.init_logger("omagent", "omagent", level="INFO")

# Set current working directory path
CURRENT_PATH = Path(__file__).parents[0]

# Import registered modules
registry.import_module(project_path=CURRENT_PATH.joinpath('agent'))

container.register_stm("RedisSTM")
# Load container configuration from YAML file
container.from_config(CURRENT_PATH.joinpath('container.yaml'))



# Initialize simple VQA workflow
workflow = ConductorWorkflow(name='ToT_test')

# Configure workflow tasks:
# 1. Input interface for user 4 numbers
client_input_task = simple_task(task_def_name='InputInterface', task_reference_name='input_task')

thought_decomposition = simple_task(task_def_name='ThoughtDecomposition', task_reference_name='thought_decomposition')

thought_generator = simple_task(task_def_name='ThoughtGenerator', task_reference_name='thought_generator')

state_evaluator = simple_task(task_def_name='StateEvaluator', task_reference_name='state_evaluator')


search_algorithm = simple_task(task_def_name='SearchAlgorithm', task_reference_name='search_algorithm')

tot_loop = DoWhileTask(task_ref_name='tot_loop', tasks=[thought_generator, state_evaluator, search_algorithm], 
                             termination_condition='if ($.search_algorithm["finish"] == true){false;} else {true;} ')



# output_interface = simple_task(task_def_name='OutputInterface', task_reference_name='output_interface')

# Configure workflow execution flow: Input -> TOT_LOOP -> Output
# workflow >> thought_decomposition >> thought_generator >> state_evaluator >> search_algorithm

workflow >> thought_decomposition >> tot_loop



# Register workflow
workflow.register(True)

# Initialize and start CLI client with workflow configuration
config_path = CURRENT_PATH.joinpath('configs')
cli_client = DefaultClient(interactor=workflow, config_path=config_path, workers=[InputInterface()])
cli_client.start_interactor()
