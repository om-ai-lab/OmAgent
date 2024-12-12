# Import required modules and components
from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.cli.client import DefaultClient
from omagent_core.utils.logger import logging

from agent.input_interface.input_interface import InputInterface

# Initialize logging
logging.init_logger("omagent", "omagent", level="INFO")
import os
os.environ['custom_openai_endpoint'] = 'http://36.133.246.107:11002/v1'
os.environ['custom_openai_key'] = 'sk-iytCHBhtNvAhtxeBC8E5A71e473c45C1B9847b6bB2F6461b'
os.environ['bing_api_key'] = '573bfabb7359487b90b8f8d26a4f6fc5'
os.environ['custom_openai_text_encoder_key'] = 'sk-2fpMc0GBGTGG96w62cF7B9621bA34aDa8b2112D26404Ae4e'

# Set current working directory path
CURRENT_PATH = Path(__file__).parents[0]

# Import registered modules
registry.import_module(project_path=CURRENT_PATH.joinpath('agent'))

container.register_stm("RedisSTM")
# Load container configuration from YAML file
container.from_config(CURRENT_PATH.joinpath('container.yaml'))



# Initialize simple VQA workflow
workflow = ConductorWorkflow(name='Internet_Meme')

# Configure workflow tasks:
# 1. Input interface for user interaction
task1 = simple_task(task_def_name='InputInterface', task_reference_name='input_task')
# # 2. Simple VQA processing based on user input
# task2 = simple_task(task_def_name='SimpleVQA', task_reference_name='simple_vqa', inputs={'user_instruction': task1.output('user_instruction')})

task2 = simple_task(task_def_name='MemeSearcher', task_reference_name='meme_searcher', inputs={'user_instruction': task1.output('user_instruction')})

task3 = simple_task(task_def_name='MemeExplain', task_reference_name='meme_explain')

# Configure workflow execution flow: Input -> VQA
workflow >> task1 >> task2 >> task3

# Register workflow
workflow.register(True)

# Initialize and start CLI client with workflow configuration
config_path = CURRENT_PATH.joinpath('configs')
cli_client = DefaultClient(interactor=workflow, config_path=config_path, workers=[InputInterface()])
cli_client.start_interactor()
