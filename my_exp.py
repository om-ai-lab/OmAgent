from omagent_core.engine.http.models import Task, TaskResult
from omagent_core.engine.http.models.task_result_status import TaskResultStatus
from omagent_core.engine.workflow.task.simple_task import SimpleTask
from omagent_core.engine.workflow.task.switch_task import SwitchTask
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.executor.workflow_executor import WorkflowExecutor
from omagent_core.engine.automator.task_handler import TaskHandler
from omagent_core.engine.configuration.configuration import Configuration
from omagent_core.engine.http.models import StartWorkflowRequest
from omagent_core.utils.compile import compile_workflow
from pathlib import Path
from time import sleep
import asyncio
from logging import Logger

from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry

# class SimpleWorker(WorkerInterface):
#     def execute(self, task: Task) -> TaskResult:
#         input_data = task.input_data
#         print(1111, input_data)
#         task_result = self.get_task_result_from_task(task)
#         task_result.add_output_data('worker_style', 'class')
#         task_result.add_output_data('secret_number', 1234)
#         task_result.add_output_data('is_it_true', False)
#         task_result.status = TaskResultStatus.COMPLETED
#         return task_result

#     def get_polling_interval_in_seconds(self) -> float:
#         # poll every 500ms
#         return 0.5

# 创建Node的运行逻辑，类型为worker，实现一个_run方法。 workflow_instance_id 就是workflow实例的唯一ID,从BaseWorker的execute的参数task里面可以获取，这儿还没想好怎么传进来
@registry.register_worker()
class SimpleWorker(BaseWorker):
    def _run(self, my_name:str, *args, **kwargs):
        print(1111111, my_name)
        return {'worker_style': 'class', 'secret_number': 1234, 'is_it_true': False}
    
@registry.register_worker()
class SimpleWorker2(BaseWorker):
    def _run(self, secret_number:int, is_it_true:bool, *args, **kwargs):
        print(22222222, is_it_true)
        secret_number += 1
        return {'num': secret_number}
    
@registry.register_worker()
class SimpleWorker3(BaseWorker):
    def _run(self, *args, **kwargs):
        print('3333333333')
        return {'switch_case_value': 1}
    
@registry.register_worker()
class SimpleWorker4(BaseWorker):
    async def _run(self, *args, **kwargs):
        # 创建多个并发任务
        async def count_task(i):
            await asyncio.sleep(1)
            print(f'Task {i} completed!')
            return i

        tasks = [count_task(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        print('All tasks completed:', results)
        return {'me': 10086, 'results': results}
    

# api_config = Configuration(base_url="http://0.0.0.0:8080")
# http://36.133.246.107:21964/workflowDef/my_exp    #这个是conductor的UI地址

# worker通过config来初始化，可以使用 omagent-core/src/omagent_core/utils/compile.py 编译worker的config模版
worker_config = {'SimpleWorker2': {'poll_interval': {'value': 100, 'description': 'Worker poll interval in millisecond', 'env_var': 'POLL_INTERVAL'}, 'domain': {'value': None, 'description': 'The domain of workflow', 'env_var': 'DOMAIN'}}, 'SimpleWorker4': {'poll_interval': {'value': 100, 'description': 'Worker poll interval in millisecond', 'env_var': 'POLL_INTERVAL'}, 'domain': {'value': None, 'description': 'The domain of workflow', 'env_var': 'DOMAIN'}}, 'SimpleWorker': {'poll_interval': {'value': 100, 'description': 'Worker poll interval in millisecond', 'env_var': 'POLL_INTERVAL'}, 'domain': {'value': None, 'description': 'The domain of workflow', 'env_var': 'DOMAIN'}}, 'SimpleWorker3': {'poll_interval': {'value': 100, 'description': 'Worker poll interval in millisecond', 'env_var': 'POLL_INTERVAL'}, 'domain': {'value': None, 'description': 'The domain of workflow', 'env_var': 'DOMAIN'}}}
task_handler = TaskHandler(worker_config=worker_config)
task_handler.start_processes()  #启动worker，监听conductor的消息




# workflow = ConductorWorkflow(name='my_exp') #初始化workflow， 代码暂时需要在 CMCC-11 上跑

# task = SimpleTask(task_def_name='SimpleWorker', task_reference_name='ref_name') #初始化task，也就是节点。task_def_name 绑定worker的类名
# task.input_parameters.update({'my_name': workflow.input('my_name')})    #设置node的输入值
# task2 = SimpleTask(task_def_name='SimpleWorker2', task_reference_name='ref_name2')
# task2.input_parameters.update({ 'secret_number': task.output('secret_number'), 'is_it_true':task.output('is_it_true')})
# task3 = SimpleTask(task_def_name='SimpleWorker3', task_reference_name='ref_name3')
# task4 = SimpleTask(task_def_name='SimpleWorker4', task_reference_name='ref_name4')
# # switch_task = SwitchTask(task_ref_name='switch_1', case_expression=task3.output('switch_case_value'))
# # switch_task.switch_case(1, task)
# # switch_task.switch_case(2, task2)

# workflow >> task3 >> {1 : task , 2 : task2} #设定workflow的运行顺序，>>是下一个节点，字典是分支，字典前面的一个节点需要在返回参数里包含一个 switch_case_value 字段，来指示走哪个分支
# # register_res = workflow.register(True)  #工作流注册到conductor
# # print(3333333333333, register_res)


workflow = ConductorWorkflow(name='my_exp')
sub_workflow = ConductorWorkflow(name='my_sub_2')

task = SimpleTask(task_def_name='SimpleWorker', task_reference_name='ref_name') #初始化task，也就是节点。task_def_name 绑定worker的类名
task.input_parameters.update({'my_name': workflow.input('my_name')})    #设置node的输入值
task2 = SimpleTask(task_def_name='SimpleWorker2', task_reference_name='ref_name2')
task2.input_parameters.update({ 'secret_number': task.output('secret_number'), 'is_it_true':task.output('is_it_true')})
task3 = SimpleTask(task_def_name='SimpleWorker3', task_reference_name='ref_name3')
task4 = SimpleTask(task_def_name='SimpleWorker4', task_reference_name='ref_name4')

sub_workflow >> task3 >> task4
workflow >> task >> sub_workflow

# workflow >> task >> task2 >> task3 >> task4

compile_workflow(workflow, Path('./'), True)

# workflow_request = StartWorkflowRequest(name=workflow.name, version=workflow.version, input={'my_name': 'Lu'})
workflow_execution_id = workflow.start_workflow_with_input(workflow_input={'my_name': 'Lu'})    #启动一个workflow实例，并运行

print(f'\nworkflow execution ID: {workflow_execution_id}\n')

while True:
    status = workflow.get_workflow(workflow_id=workflow_execution_id).status    #获取执行状态
    if status == 'COMPLETED':
        break
    sleep(0.1)
    print(11111)

result = workflow.get_workflow(workflow_id=workflow_execution_id)   #获取执行结果

print(f'\nworkflow result: {result.output}\n')

task_handler.stop_processes()