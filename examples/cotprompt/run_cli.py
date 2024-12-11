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
from pathlib import Path
logging.init_logger("omagent", "omagent", level="INFO")

# 设置当前工作目录路径
CURRENT_PATH = Path(__file__).parents[0]

# 注册worker
registry.import_module(project_path=CURRENT_PATH.joinpath('agent'))
container.register_stm("RedisSTM")
container.from_config(CURRENT_PATH.joinpath('container.yaml'))

# 初始化工作流
workflow = ConductorWorkflow(name='cot_algorithm_workflow')

# 任务1: 输入接口任务
client_input_task = simple_task(task_def_name='COTInputInterface', task_reference_name='cot_input_interface')

# 任务2: 设置 user_question 变量
# init_set_variable_task = SetVariableTask(
#     task_ref_name='init_set_variable_task', 
#     input_parameters={'user_question': client_input_task.output('user_question')}
# )

# 任务3: 推理生成任务
reasoning_task = simple_task(task_def_name='COTReasoning', task_reference_name='cot_reasoning', inputs={'user_question': client_input_task.output('user_question')})

# 任务4: 设置推理结果变量
# set_reasoning_result_task = SetVariableTask(
#     task_ref_name='set_reasoning_result_task', 
#     input_parameters={'reasoning_result': reasoning_task.output('reasoning_result')}
# )

# 任务5: 生成最终答案
conclude_task = simple_task(task_def_name='COTConclusion', task_reference_name='cot_conclude', inputs={'user_question':  client_input_task.output('user_question'), 'reasoning_result': reasoning_task.output('reasoning_result')})

# 定义工作流执行顺序: 输入 -> 设置 user_question -> 推理生成 -> 结论生成
workflow >> client_input_task  >> reasoning_task  >> conclude_task

# 注册工作流
workflow.register(overwrite=True)

# 启动应用
config_path = CURRENT_PATH.joinpath('configs')
cli_client = DefaultClient(interactor=workflow, config_path=config_path, workers=[COTInputInterface()])
cli_client.start_interactor()
