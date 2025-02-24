import os
os.environ['OMAGENT_MODE'] = 'lite'



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

from omagent_core.clients.devices.programmatic import ProgrammaticClient

from agent.input_interface.input_interface import InputInterfaceGot
from omagent_core.advanced_components.workflow.general_got.workflow import GoTWorkflow

# Initialize logging
logging.init_logger("omagent", "omagent", level="INFO")

# Set current working directory path
CURRENT_PATH = Path(__file__).parents[0]

# Import registered modules
registry.import_module(project_path=CURRENT_PATH.joinpath('agent'))
container.register_stm("SharedMemSTM")
# Load container configuration from YAML file
container.from_config(CURRENT_PATH.joinpath('container.yaml'))

# Initialize the main GoT  workflow
workflow = ConductorWorkflow(name='GoTprogrammatic')
got_workflow = GoTWorkflow()
got_workflow.set_input(query=workflow.input('query'), task=workflow.input('task'), meta=workflow.input('meta'))
workflow >> got_workflow
workflow.register(overwrite=True)

# Initialize programmatic client
config_path = CURRENT_PATH.joinpath('configs')
programmatic_client = ProgrammaticClient(processor=workflow, config_path=config_path)

# Prepare batch processing inputs
# sort example
workflow_input_list = [
    {"query": "[6, 3, 6, 5, 1, 2, 4, 3, 8, 0, 7, 8, 6, 4, 9, 5, 2, 4, 8, 4, 4, 4, 5, 6, 8, 4, 7, 7, 8, 9, 4, 9]", "task": "sort", "meta": None}
]

# #keyword_count example
# workflow_input_list = [
#     {"query": "One evening, Sarah, an archaeologist from Norway made a surprising discovery about ancient trade routes between Sweden and Norway. As per her research, the artifacts that were found in Norway were identical to those in Sweden, indicating a deep-rooted cultural connection between Sweden and Norway. This piqued the interest of her colleague, James, who was from Canada.", "task": "keyword_count", "meta": {'all_possible_countries': ["Norway", "Sweden", "Canada"]}}
# ]
    
# #set_intersection example
# workflow_input_list = [
#     {"query": '{"set1": [11, 60, 1, 49, 21, 33, 14, 56, 54, 15, 23, 40, 45, 22, 7, 28, 20, 46, 51, 6, 34, 37, 3, 50, 17, 8, 25, 0, 35, 47, 18, 19], "set2": [31, 11, 4, 63, 38, 58, 59, 24, 61, 14, 32, 39, 27, 46, 48, 19, 52, 57, 50, 56, 3, 2, 53, 29, 5, 37, 62, 41, 36, 12, 49, 16]}', "task": "set_intersection", "meta": None}
# ]

# workflow_input_list = [{"query": "Find intersection of two sets: Set A [1,2,3,4,5,6,7,8,9,10,11,12`] and Set B [2,4,6,8,10,12,14,16]", "task": None, "meta": None}]
# workflow_input_list = [{"query": "Help me to sort the following list: [6, 3, 6, 5, 1, 2, 4, 3, 8, 0, 7, 8, 6, 4, 9, 5, 2, 4, 8, 4, 4, 7, 7, 8, 9] in descending order", "task": None, "meta": None}]
# workflow_input_list = [{"query": "Count the number of times each country is mentioned in the following text: 'One evening, Sarah, an archaeologist from Norway made a surprising discovery about ancient trade routes between Sweden and Norway. As per her research, the artifacts that were found in Norway were identical to those in Sweden, indicating a deep-rooted cultural connection between Sweden and Norway. This piqued the interest of her colleague, James, who was from Canada.' return the result in a json format", "task": None, "meta": None}]


# Process questions in batches
res = programmatic_client.start_batch_processor(workflow_input_list=workflow_input_list)
print(res)

# Cleanup
programmatic_client.stop_processor()