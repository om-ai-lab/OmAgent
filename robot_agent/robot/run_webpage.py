# Import required modules and components
import os
os.environ["OMAGENT_MODE"] = "pro"


from pathlib import Path

from omagent_core.clients.devices.webpage.client import WebpageClient
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.utils.container import container
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry


# Initialize logging
logging.init_logger("omagent", "omagent", level="INFO")

# Set current working directory path
CURRENT_PATH = Path(__file__).parents[0]

# Import registered modules
registry.import_module(project_path=CURRENT_PATH.joinpath("agent"))

container.register_stm("RedisSTM")
# Load container configuration from YAML file
container.from_config(CURRENT_PATH.joinpath("container.yaml"))


# Initialize simple VQA workflow
workflow = ConductorWorkflow(name="robot")
#workflow_path = "RobotNavigationWorkflow_workflow.json"
workflow_path = "FastReActRobotWorkflow_workflow.json"

workflow.load(workflow_path)


# Configure workflow tasks:
# 1. Input interface for user interaction
# Register workflow
workflow.register(True)

# Initialize and start app client with workflow configuration
config_path = CURRENT_PATH.joinpath("configs")
agent_client = WebpageClient(
    interactor=workflow, config_path=config_path, workers=[]
)
agent_client.start_interactor()
