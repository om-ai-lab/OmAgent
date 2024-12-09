# Import core modules for workflow management and configuration
from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.utils.logger import logging

logging.init_logger( "omagent", "omagent", level="INFO" )

# Import registry and CLI client modules
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.app.client import AppClient

from pathlib import Path

CURRENT_PATH = Path( __file__ ).parents[ 0 ]

# Import and register worker modules from agent directory
registry.import_module( project_path=CURRENT_PATH.joinpath( 'agent' ) )

# Add parent directory to Python path
import sys
import os

sys.path.append( os.path.abspath( CURRENT_PATH.joinpath( '../../' ) ) )

# Import custom image input worker
from agent.input_interface.input_interface import InputInterface

# Configure Redis storage and load container settings
container.register_stm( "RedisSTM" )
container.from_config( CURRENT_PATH.joinpath( 'container.yaml' ) )

# Initialize ai explainer workflow
workflow = ConductorWorkflow( name='ai_explainer' )

# Define workflow tasks:
# 1. Get sight or artifact image from user
task1 = simple_task( task_def_name='InputInterface', task_reference_name='image_input' )

# 2. Query sight or artifact name
task2 = simple_task( task_def_name='QuerySightOrArtifact', task_reference_name='query_sight_or_artifact' )

# 3. Search for sight or artifact information
task3 = simple_task( task_def_name='SearchSightOrArtifact', task_reference_name='search_sight_or_artifact' )

# 4. Generate sight or artifact explanation
task4 = simple_task( task_def_name='GenerateExplanation', task_reference_name='generate_explanation' )

# Configure workflow execution flow: Input -> VQA
workflow >> task1 >> task2 >> { 1: [ task3, task4 ]}

# Register workflow
workflow.register( True )

# Initialize and start app client with workflow configuration
config_path = CURRENT_PATH.joinpath( 'configs' )
cli_client = AppClient( interactor=workflow, config_path=config_path, workers=[ InputInterface() ] )
cli_client.start_interactor()
