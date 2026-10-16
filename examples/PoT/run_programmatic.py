# Import core modules and components for the Program of Thought (PoT) workflow
import os
os.environ["OMAGENT_MODE"] = "lite"

from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.advanced_components.workflow.pot.workflow import PoTWorkflow
from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.programmatic import ProgrammaticClient
from omagent_core.utils.logger import logging


# Initialize logging with INFO level
logging.init_logger("omagent", "omagent", level="INFO")

# Get the root directory path
CURRENT_PATH = Path(__file__).parents[0]

# Load custom agent modules from the project directory
registry.import_module(project_path=CURRENT_PATH.joinpath('agent'))

container.register_stm("SharedMemSTM")

# Load container configuration from YAML file
container.from_config(CURRENT_PATH.joinpath('container.yaml'))


# Initialize the main Program of Thought workflow
workflow = ConductorWorkflow(name='PoT')
pot_workflow = PoTWorkflow()
pot_workflow.set_input(query=workflow.input('query'), examples=workflow.input('examples'))
workflow >> pot_workflow
workflow.register(overwrite=True)

# Initialize programmatic client
config_path = CURRENT_PATH.joinpath('configs')
programmatic_client = ProgrammaticClient(processor=workflow, config_path=config_path)

# Prepare batch processing inputs
workflow_input_list = [
    {"query": "Tom gets 4 car washes a month.  If each car wash costs $15 how much does he pay in a year?", "examples": None, "options": None}
]

# Process questions in batches
res = programmatic_client.start_batch_processor(workflow_input_list=workflow_input_list, max_tasks=5)

print(res)

# Cleanup
programmatic_client.stop_processor()