# Import required modules and components
import os
os.environ["OMAGENT_MODE"] = "pro"

from pathlib import Path

from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.utils.container import container
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry

logging.init_logger("omagent", "omagent", level="INFO")

# Import agent-specific components
#from agent.input_interface.input_interface import InputInterface
from omagent_core.clients.devices.react_webpage.react_client import ReactClient

# Set current working directory path
CURRENT_PATH = root_path = Path(__file__).parents[0]

# Import registered modules
registry.import_module(project_path=CURRENT_PATH.joinpath("agent"))

container.register_stm("RedisSTM")
# Load container configuration from YAML file
container.from_config(CURRENT_PATH.joinpath("container.yaml"))

# Initialize simple VQA workflow
workflow = ConductorWorkflow(name="robot")
workflow_path = "RobotNavigationWorkflow_workflow.json"

workflow.load(workflow_path)

# Configure workflow tasks:
# 1. Input interface for user interaction

# Register workflow
workflow.register(True)

# Path to React static build
static_build_path = CURRENT_PATH.joinpath("static_build")

# Check if static build exists
if not os.path.exists(static_build_path):
    logging.warning(f"Static build folder not found at {static_build_path}. API will run without static file serving.")
    static_build_path = None

# Initialize and start React client with workflow configuration
config_path = CURRENT_PATH.joinpath("configs")
agent_client = ReactClient(
    interactor=workflow, 
    config_path=config_path, 
    workers=[],
    static_folder=static_build_path
)

print("Starting OmAgent React API server...")
print("API is available at http://localhost:8088/api")
if static_build_path:
    print("React frontend is available at http://localhost:8088")
    
agent_client.start_interactor(host="0.0.0.0", port=8088) 
