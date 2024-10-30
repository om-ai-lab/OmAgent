from omagent_core.engine.http.models import Task, TaskResult
from omagent_core.engine.http.models.task_result_status import TaskResultStatus
from omagent_core.engine.workflow.task.simple_task import SimpleTask
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.executor.workflow_executor import WorkflowExecutor
from omagent_core.engine.automator.task_handler import TaskHandler
from omagent_core.engine.configuration.configuration import Configuration
from omagent_core.engine.http.models import StartWorkflowRequest
from time import sleep

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
@registry.register_worker()
class SimpleWorker(BaseWorker):
    def _run(self, my_name:str):
        print(22222222, my_name)
        return {'worker_style': 'class', 'secret_number': 1234, 'is_it_true': False}
    

api_config = Configuration(base_url="http://0.0.0.0:8080")
# http://36.133.246.107:21964/workflowDef/my_exp

# worker = SimpleWorker()
# task_handler = TaskHandler(configuration=api_config, workers=[worker], scan_for_annotated_workers=False)
worker_config = {'SimpleWorker': {'poll_interval': {'value': 100, 'description': 'Worker poll interval in millisecond', 'env_var': 'POLL_INTERVAL'}, 'domain': {'value': None, 'description': 'The domain of workflow', 'env_var': 'DOMAIN'}}}
task_handler = TaskHandler(configuration=api_config,worker_config=worker_config)
task_handler.start_processes()




workflow_executor = WorkflowExecutor(configuration=api_config)
workflow = ConductorWorkflow(name='my_exp', executor=workflow_executor)

task = SimpleTask(task_def_name='SimpleWorker', task_reference_name='ref_name')
task.input_parameters.update({'my_name': workflow.input('my_name')})
workflow >> task
register_res = workflow.register(True)
print(3333333333333, register_res)

workflow_request = StartWorkflowRequest(name=workflow.name, version=workflow.version, input={'my_name': 'Lu'})
workflow_execution_id = workflow_executor.start_workflow(workflow_request)

print(f'\nworkflow execution ID: {workflow_execution_id}\n')

while True:
    status = workflow_executor.get_workflow(workflow_id=workflow_execution_id).status
    if status == 'COMPLETED':
        break
    sleep(0.1)
    print(11111)

result = workflow_executor.get_workflow(workflow_id=workflow_execution_id)

print(f'\nworkflow result: {result.output}\n')
print(f'see the workflow execution here: {api_config.ui_host}/execution/{result.workflow_id}\n')

task_handler.stop_processes()