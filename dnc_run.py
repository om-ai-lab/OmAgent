from omagent_core.utils.container import container
from omagent_core.engine.configuration.configuration import Configuration
container.register_connector(name='conductor_config', connector=Configuration)
from omagent_core.engine.http.models import Task, TaskResult
from omagent_core.engine.http.models.task_result_status import TaskResultStatus
from omagent_core.engine.workflow.task.simple_task import SimpleTask,simple_task
from omagent_core.engine.workflow.task.switch_task import SwitchTask
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.fork_task import ForkTask
from omagent_core.engine.workflow.task.do_while_task import DoWhileTask, LoopTask, DnCLoopTask
from omagent_core.engine.workflow.executor.workflow_executor import WorkflowExecutor
from omagent_core.engine.automator.task_handler import TaskHandler
from omagent_core.engine.http.models import StartWorkflowRequest
from omagent_core.utils.compile import compile
from omagent_core.models.llms.base import BaseLLMBackend, BaseLLM
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from omagent_core.models.llms.prompt.parser import StrParser
from pathlib import Path
from time import sleep
import asyncio
from omagent_core.utils.logger import logging
from typing import List,Any
from pydantic import Field
import yaml
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
from omagent_core.engine.task.agent_task import TaskTree
import os
from omagent_core.utils.build import build_from_file
from omagent_core.memories.stms.stm_redis import RedisSTM
from omagent_core.engine.workflow.task.set_variable_task import SetVariableTask
from PIL import Image
from pathlib import Path
from omagent_core.clients.devices.app.input import AppInput
from omagent_core.clients.devices.app.callback import AppCallback

logging.init_logger("omagent", "omagent", level="INFO")


registry.import_module()
container.register_stm(stm='RedisSTM')
container.register_callback(callback=AppCallback)
container.register_input(input=AppInput)
stm = container.get_component('RedisSTM')
stm.clear()


workflow = ConductorWorkflow(name='dnc')


tree = TaskTree()
tree.add_node({"task": "Help me to find the latest news about huawei from news websites around world and write a conclusion report about how people around world view huawei."})
# agent_task = AgentTask(id=0, task="先识别一下图片中狗的品种，然后用Websearch帮我搜索一下这条狗的信息")
# stm['image_cache'] = {"<image_0>": Image.open('/Users/heting/Downloads/dog.jpeg')}
client_input_task = simple_task(task_def_name='ClientInput', task_reference_name='client_input')
init_set_variable_task = SetVariableTask(task_ref_name='set_variable_task', input_parameters={'agent_task': client_input_task.output('agent_task'), 'last_output': client_input_task.output('last_output')})
# init_set_variable_task = SetVariableTask(task_ref_name='set_variable_task', input_parameters={'agent_task': tree.model_dump(), 'last_output': ''})
conqueror_task = simple_task(task_def_name='TaskConqueror', task_reference_name='task_conqueror', inputs={'agent_task': '${workflow.variables.agent_task}', 'last_output': '${workflow.variables.last_output}'})
divider_task = simple_task(task_def_name='TaskDivider', task_reference_name='task_divider', inputs={'agent_task': conqueror_task.output('agent_task'), 'last_output': conqueror_task.output('last_output')})
rescue_task = simple_task(task_def_name='TaskRescue', task_reference_name='task_rescue', inputs={'agent_task': conqueror_task.output('agent_task'), 'last_output': conqueror_task.output('last_output')})
divider_update_set_variable_task = SetVariableTask(task_ref_name='divider_update_set_variable_task', input_parameters={'agent_task': '${task_divider.output.agent_task}', 'last_output': '${task_divider.output.last_output}'})
conqueror_update_set_variable_task = SetVariableTask(task_ref_name='conqueror_update_set_variable_task', input_parameters={'agent_task': '${task_conqueror.output.agent_task}', 'last_output': '${task_conqueror.output.last_output}'})
conclude_task = simple_task(task_def_name='Conclude', task_reference_name='task_conclude', inputs={'agent_task': '${task_exit_monitor.output.agent_task}', 'last_output': '${task_exit_monitor.output.last_output}'})

switch_task = SwitchTask(task_ref_name='switch_task', case_expression=conqueror_task.output('switch_case_value'))
switch_task.default_case([conqueror_update_set_variable_task])
switch_task.switch_case("complex", [divider_task, divider_update_set_variable_task])
switch_task.switch_case("failed", rescue_task)

task_exit_monitor_task = simple_task(task_def_name='TaskExitMonitor', task_reference_name='task_exit_monitor', inputs={'agent_task': '${workflow.variables.agent_task}', 'last_output': '${workflow.variables.last_output}'})
post_set_variable_task = SetVariableTask(task_ref_name='post_set_variable_task', input_parameters={'agent_task': '${task_exit_monitor.output.agent_task}', 'last_output': '${task_exit_monitor.output.last_output}'})

dncloop_task = DnCLoopTask(task_ref_name='dncloop_task', tasks=[conqueror_task, switch_task], post_loop_exit=[task_exit_monitor_task, post_set_variable_task])


workflow >> client_input_task >> init_set_variable_task >> dncloop_task >> conclude_task
# workflow >> init_set_variable_task >> dncloop_task >> conclude_task

compile(workflow, Path('./'), True)

# worker通过config来初始化，可以使用 omagent-core/src/omagent_core/utils/compile.py 编译worker的config模版

worker_config = build_from_file('examples/dnc_loop/configs')
task_handler = TaskHandler(worker_config=worker_config)
task_handler.start_processes()  #启动worker，监听conductor的消息

# workflow_execution_id = workflow.start_workflow_with_input()    #启动一个workflow实例，并运行

# print(f'\nworkflow execution ID: {workflow_execution_id}\n')

# while True:
#     status = workflow.get_workflow(workflow_id=workflow_execution_id).status    #获取执行状态
#     if status == 'COMPLETED':
#         break

# result = workflow.get_workflow(workflow_id=workflow_execution_id)   #获取执行结果

# print(f'\nworkflow result: {result.output}\n')

# task_handler.stop_processes()