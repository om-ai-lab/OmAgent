from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.programmatic import ProgrammaticClient
from omagent_core.utils.logger import logging
from omagent_core.advanced_components.workflow.react_pro.workflow import ReactProWorkflow

logging.init_logger("omagent", "omagent", level="INFO")

# Set current working directory path
CURRENT_PATH = Path(__file__).parents[0]

# Import registered modules
registry.import_module(CURRENT_PATH.joinpath('agent'))

# Load container configuration from YAML file
container.register_stm("SharedMemSTM")
container.from_config(CURRENT_PATH.joinpath('container.yaml'))

# Initialize workflow
workflow = ConductorWorkflow(name='react_pro_example')

# Configure React Pro workflow
react_pro_workflow = ReactProWorkflow()
react_pro_workflow.set_input(
    query=workflow.input('query'),
    id=workflow.input('id')
)

# Configure workflow execution flow
workflow >> react_pro_workflow 

# Register workflow
workflow.register(overwrite=True)

# Initialize programmatic client
config_path = CURRENT_PATH.joinpath('configs')
programmatic_client = ProgrammaticClient(
    processor=workflow,
    config_path=config_path,
    workers=[]  # No additional workers needed for React Pro workflow
)

# Prepare input data
workflow_input_list = [
    {
        "query": "When was Albert Einstein born?", 
        "id": "test_1"
    }
]

print(f"\nProcessing query: {workflow_input_list[0]['query']}")
print(f"Query ID: {workflow_input_list[0]['id']}\n")

res = programmatic_client.start_batch_processor(
    workflow_input_list=workflow_input_list
)

programmatic_client.stop_processor()

# Print results
print(res)