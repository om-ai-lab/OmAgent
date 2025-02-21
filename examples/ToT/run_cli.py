from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.advanced_components.workflow.ToT.workflow import ToTWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.cli import DefaultClient
from omagent_core.utils.logger import logging
from agent.tot_input.tot_input import ToTInput
from agent.tot_output.tot_output import ToTOutput

# Initialize logging configuration
logging.init_logger("omagent", "omagent", level="INFO")

# Set current working directory path
CURRENT_PATH = Path(__file__).parents[0]

# Import registered modules from agent directory
registry.import_module(project_path=CURRENT_PATH.joinpath('agent'))

# Configure storage and container settings
container.register_stm("SharedMemSTM")
container.from_config(CURRENT_PATH.joinpath('container.yaml'))

# Initialize main workflow
workflow = ConductorWorkflow(name='ToT_Workflow')

# Configure input task
tot_input = simple_task(
    task_def_name=ToTInput, 
    task_reference_name="tot_input",
)

# Initialize and configure ToT workflow
tot_workflow = ToTWorkflow()
tot_workflow.set_tot(
    requirements = tot_input.output("requirements"),  # Set requirements from input
)
tot_workflow.set_input(
    query = tot_input.output("query"),  # Set query from input
)

# Configure output task
tot_output = simple_task(
    task_def_name=ToTOutput, 
    task_reference_name="tot_output", 
    inputs={
        "result": tot_workflow.result,  # Pass workflow results to output
    }
)

# Define workflow execution sequence
workflow >> tot_input >> tot_workflow >> tot_output

# Register workflow for execution
workflow.register(True)

# Initialize and start CLI client
config_path = CURRENT_PATH.joinpath('configs')
cli_client = DefaultClient(
    interactor=workflow, 
    config_path=config_path, 
    workers=[]
)
cli_client.start_interactor()