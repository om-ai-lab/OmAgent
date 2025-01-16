# Import required modules and components
import os
from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from pathlib import Path
from omagent_core.utils.registry import registry
#from omagent_core.clients.devices.cli.client import DefaultClient
from omagent_core.clients.devices.lite_version.cli import DefaultClient
from omagent_core.utils.logger import logging
from agent.input_interface.input_interface import InputInterface
from omagent_core.advanced_components.workflow.cot.workflow import CoTWorkflow
from omagent_core.engine.worker.base import BaseWorker
from colorama import Fore
import json

@registry.register_worker()
class SimpleInput(BaseWorker):
    def _run(self, query, *args, **kwargs):
        cot_method = input(f"\n{Fore.GREEN}Enter cot_method (type 'few_shot' or zero_shot): ")
        assert cot_method in [ 'few_shot', 'zero_shot' ], "Invalid method provided"        
        if cot_method == 'few_shot':
            message = input(f"\nIf using few_shot method, please provide your examples (in the order of question, reasoning, answer). If using zero_shot, please press enter to skip:")            
            cot_examples = [
                    {
                        "q": example[ 0 ][ 'data' ],
                        "r": example[ 1 ][ 'data' ],
                        "a": example[ 2 ][ 'data' ]
                    } for example in
                    [ message[ i : i + 3 ] for i in range( 0, len( message ), 3 ) ]
                ]
            
        else:
            cot_examples = []
        logging.info(
            f"InputInterface: query={query}, cot_method={cot_method}, cot_examples={cot_examples}"
        )
        return {"query":query, "cot_method":cot_method, "cot_examples":cot_examples }

logging.init_logger("omagent", "omagent", level="INFO")

# Set current working directory path
CURRENT_PATH = root_path = Path(__file__).parents[0]

# Import registered modules
registry.import_module(CURRENT_PATH.joinpath('agent'))

# Load container configuration from YAML file
container.register_stm("SharedMemSTM")
#container.from_config(CURRENT_PATH.joinpath('container.yaml'))

# Initialize simple VQA workflow
workflow = ConductorWorkflow(name='cot', lite_version=True)

# Configure workflow tasks:
# 1. Input interface for user interaction
client_input_task = simple_task(task_def_name=SimpleInput, task_reference_name='input_interface')

cot_workflow = CoTWorkflow()
cot_workflow.set_input(query=client_input_task.output('query'), cot_method=client_input_task.output('cot_method'), cot_examples=client_input_task.output('cot_examples'))

workflow >> client_input_task >> cot_workflow

# Register workflow
workflow.register(overwrite=True)

# Initialize and start app client with workflow configuration
config_path = CURRENT_PATH.joinpath('configs')
cli_client = DefaultClient(interactor=workflow, config_path=config_path, workers=[SimpleInput()])
cli_client.start_interaction()

