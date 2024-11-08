
from examples.step1_simpleVQA.agent.simple_vqa.simple_vqa import SimpleVQA
from omagent_core.services.connectors.redis import RedisConnector
from omagent_core.utils.container import container
from omagent_core.engine.configuration.configuration import Configuration
container.register_connector(name='conductor_config', connector=Configuration)
container.register_connector(name='redis_stream_client', connector=RedisConnector)
from omagent_core.clients.devices.cli.client import DefaultClient

from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from pathlib import Path
import yaml
from omagent_core.engine.automator.task_handler import TaskHandler

from omagent_core.memories.stms.stm_dict import DictSTM
from omagent_core.memories.stms.stm_deque import DequeSTM
from omagent_core.memories.stms.stm_redis import RedisSTM
from omagent_core.utils.registry import registry
from omagent_core.utils.build import build_from_file
from omagent_core.clients.devices.app.client import AppClient
from omagent_core.clients.devices.app.callback import AppCallback
from omagent_core.clients.devices.app.input import AppInput
from omagent_core.utils.logger import logging

logging.init_logger("omagent", "omagent", level="INFO")

registry.import_module()

container.register_stm(stm='RedisSTM')
container.register_callback(callback='AppCallback')
container.register_input(input='AppInput')
import sys
import os
from pathlib import Path
CURRENT_PATH = Path(__file__).parents[0]
sys.path.append(os.path.abspath(CURRENT_PATH.joinpath('../../')))

workflow = ConductorWorkflow(name='example1')

# task1 = simple_task(task_def_name='RedisStreamListener', task_reference_name='input_task')
task2 = simple_task(task_def_name='SimpleVQA', task_reference_name='simple_vqa')

workflow >> task2

agent_client = AppClient(interactor=workflow)
# agent_client.compile()
agent_client.start_interactor()
