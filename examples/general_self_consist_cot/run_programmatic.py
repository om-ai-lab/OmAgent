# Import required modules and components
import os
from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.programmatic import ProgrammaticClient
from omagent_core.utils.logger import logging
from omagent_core.advanced_components.workflow.self_consist_cot.workflow import SCCoTWorkflow

logging.init_logger("omagent", "omagent", level="INFO")

# Set current working directory path
CURRENT_PATH = Path(__file__).parents[0]

# Load num_path configuration
config_path = CURRENT_PATH.joinpath('configs')

# Import registered modules
registry.import_module(CURRENT_PATH.joinpath('agent'))

# Load container configuration from YAML file
container.register_stm("SharedMemSTM")
container.from_config(CURRENT_PATH.joinpath('container.yaml'))

# Initialize workflow
workflow = ConductorWorkflow(name='general_self_consist_cot')

# Configure Self Consistent COT workflow
self_consist_cot_workflow = SCCoTWorkflow()
self_consist_cot_workflow.set_input(
    query=workflow.input('query')
)

# Configure workflow execution flow
workflow >> self_consist_cot_workflow

# Register workflow
workflow.register(overwrite=True)

# Initialize programmatic client
programmatic_client = ProgrammaticClient(
    processor=workflow,
    config_path=config_path,
    workers=[]  # No additional workers needed
)

# Prepare input data
workflow_input_list = [
    {
        "query": "Which is bigger, 9.9 or 9.11?"
    }
]


res = programmatic_client.start_batch_processor(
    workflow_input_list=workflow_input_list
)

programmatic_client.stop_processor()

# Print results
print(res)
