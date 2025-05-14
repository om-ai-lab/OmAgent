from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.programmatic import ProgrammaticClient
from omagent_core.utils.logger import logging
from omagent_core.advanced_components.workflow.react.workflow import ReactWorkflow

logging.init_logger("omagent", "omagent", level="INFO")

# Set current working directory path
CURRENT_PATH = Path(__file__).parents[0]

# Import registered modules
registry.import_module(CURRENT_PATH.joinpath('agent'))

# Load container configuration from YAML file
container.register_stm("SharedMemSTM")
container.from_config(CURRENT_PATH.joinpath('container.yaml'))

# Initialize workflow
workflow = ConductorWorkflow(name='react_workflow_example')

# Configure React Basic workflow
react_workflow = ReactWorkflow()
react_workflow.set_input(
    query=workflow.input('query'),
    id=workflow.input('id')
)

# Configure workflow execution flow
workflow >> react_workflow 

# Register workflow
workflow.register(overwrite=True)

# Initialize programmatic client
config_path = CURRENT_PATH.joinpath('configs')
programmatic_client = ProgrammaticClient(
    processor=workflow,
    config_path=config_path,
    workers=[]  # No additional workers needed for React workflow
)

# Prepare input data
workflow_input_list = [
    {
        "query": "When was Albert Einstein born?", 
        "id": "21"
    }
]

res = programmatic_client.start_batch_processor(
    workflow_input_list=workflow_input_list
)

programmatic_client.stop_processor()
