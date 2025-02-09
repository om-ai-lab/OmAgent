import os
os.environ["custom_openai_key"] = "notneeded"
os.environ["custom_openai_endpoint"] = "http://140.207.201.47:11434/v1"
os.environ["custom_openai_model_id"] = "qwen2.5:7b"
os.environ['HTTP_PROXY'] = 'http://10.8.21.200:47890'
os.environ['HTTPS_PROXY'] = 'http://10.8.21.200:47890'

from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.lite_version.cli import DefaultClient
from omagent_core.utils.logger import logging
from omagent_core.advanced_components.workflow.reflexion.workflow import ReflexionWorkflow
from agent.input_interface.input_interface import InputInterface
from omagent_core.engine.worker.base import BaseWorker


@registry.register_worker()
class SimpleInterface(BaseWorker):
    def _run(self, query, *args, **kwargs):
        return {"query": query}


logging.init_logger("omagent", "omagent", level="INFO")

# Set current working directory path
CURRENT_PATH = Path(__file__).parents[0]

# Import registered modules
registry.import_module(CURRENT_PATH.joinpath('agent'))

# Load container configuration from YAML file
container.register_stm("SharedMemSTM")
#container.from_config(CURRENT_PATH.joinpath('container.yaml'))

# Initialize workflow
workflow = ConductorWorkflow(name='reflexion', lite_version=True)

# Configure input task
input_task = simple_task(
    task_def_name=SimpleInterface,
    task_reference_name='input_interface'
)

# Configure React Pro Reflexion workflow
react_workflow = ReflexionWorkflow()
react_workflow.set_input(
    query=input_task.output('query')
)

# Configure workflow execution flow
workflow >> input_task >> react_workflow

# Register workflow
workflow.register(overwrite=True)

# Initialize and start CLI client
config_path = CURRENT_PATH.joinpath('configs')
cli_client = DefaultClient(
    interactor=workflow, config_path=config_path, workers=[SimpleInterface()]
)

query = "法国的首都是哪里"
cli_client.start_processor_with_input({"query": query})
