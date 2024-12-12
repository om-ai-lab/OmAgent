from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.cli.client import DefaultClient
from omagent_core.utils.logger import logging
from omagent_core.engine.workflow.task.set_variable_task import SetVariableTask

from agent.cot_input_interface.cot_input_interface import COTInputInterface
from agent.cot_reasoning.cot_reasoning import COTReasoning
from agent.cot_conclude.cot_conclude import COTConclusion
from agent.cot_extract.cot_extract import COTExtract
from pathlib import Path
logging.init_logger("omagent", "omagent", level="INFO")

CURRENT_PATH = Path(__file__).parents[0]

registry.import_module(project_path=CURRENT_PATH.joinpath('agent'))
container.register_stm("RedisSTM")
container.from_config(CURRENT_PATH.joinpath('container.yaml'))

workflow = ConductorWorkflow(name='cot_algorithm_workflow')

client_input_task = simple_task(task_def_name='COTInputInterface', task_reference_name='cot_input_interface')

reasoning_task = simple_task(task_def_name='COTReasoning', task_reference_name='cot_reasoning', inputs={'user_question': client_input_task.output('user_question'),'path_num':client_input_task.output('path_num')})

extract_task = simple_task(task_def_name='COTExtract', task_reference_name='cot_extract', inputs={'reasoning_result': reasoning_task.output('reasoning_result')})

conclude_task = simple_task(task_def_name='COTConclusion', task_reference_name='cot_conclude', inputs={'final_answer': extract_task.output('final_answer')})

workflow >> client_input_task  >> reasoning_task  >>  extract_task >> conclude_task

workflow.register(overwrite=True)

config_path = CURRENT_PATH.joinpath('configs')
cli_client = DefaultClient(interactor=workflow, config_path=config_path, workers=[COTInputInterface()])
cli_client.start_interactor()
