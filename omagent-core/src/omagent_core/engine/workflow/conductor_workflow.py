import itertools
from copy import deepcopy
from typing import Any, Dict, List, Union

from omagent_core.engine.http.models import *
from omagent_core.engine.workflow.executor.local_workflow_executor import WorkflowExecutor as LiteWorkflowExecutor
from omagent_core.engine.http.models.start_workflow_request import \
    IdempotencyStrategy
from omagent_core.engine.orkes.orkes_workflow_client import workflow_client
from omagent_core.engine.workflow.executor.workflow_executor import \
    WorkflowExecutor
from omagent_core.engine.workflow.task.fork_task import ForkTask
from omagent_core.engine.workflow.task.join_task import JoinTask
from omagent_core.engine.workflow.task.set_variable_task import SetVariableTask
from omagent_core.engine.workflow.task.switch_task import SwitchTask
from omagent_core.engine.workflow.task.do_while_task import DoWhileTask
from omagent_core.engine.workflow.task.task import TaskInterface
from omagent_core.engine.workflow.task.task_type import TaskType
from omagent_core.engine.workflow.task.timeout_policy import TimeoutPolicy
from omagent_core.utils.container import container
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
from shortuuid import uuid
from typing_extensions import Self
import os
from omagent_core.engine.http.models.workflow_def import to_workflow_def
from omagent_core.engine.workflow.task.simple_task import simple_task

class ConductorWorkflow:
    SCHEMA_VERSION = 2

    def __init__(self, name: str, version: int = None, description: str = None, lite_version: bool = False) -> Self:
        if lite_version or os.getenv("OMAGENT_MODE") == "lite":
            print ("lite mode")
            self._executor = LiteWorkflowExecutor()
        else:
            print ("pro mode")
            self._executor = WorkflowExecutor()
        self.name = name
        self.version = version
        self.description = description
        self.lite_version = lite_version
        self._tasks = []
        self._owner_email = "default@omagent.ai"
        self._timeout_policy = None
        self._timeout_seconds = 60
        self._failure_workflow = ""
        self._input_parameters = []
        self._output_parameters = {}
        self._input_template = {}
        self._variables = {}
        self._restartable = True
        self._workflow_status_listener_enabled = False
        self._workflow_status_listener_sink = None
        if container.conductor_config.debug:
            self.stop_all_running_workflows()

    def initialization(self, worker_config):
        for config in worker_config:
            worker_cls = registry.get_worker(config['name'])
            self.workers[config['name']] = worker_cls(**config)
        return self.workers

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        if not isinstance(name, str):
            raise Exception("invalid type")
        self._name = deepcopy(name)

    @property
    def version(self) -> int:
        return self._version

    @version.setter
    def version(self, version: int) -> None:
        if version != None and not isinstance(version, int):
            raise Exception("invalid type")
        self._version = deepcopy(version)

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, description: str) -> None:
        if description != None and not isinstance(description, str):
            raise Exception("invalid type")
        self._description = deepcopy(description)

    def timeout_policy(self, timeout_policy: TimeoutPolicy) -> Self:
        if not isinstance(timeout_policy, TimeoutPolicy):
            raise Exception("invalid type")
        self._timeout_policy = deepcopy(timeout_policy)
        return self

    def timeout_seconds(self, timeout_seconds: int) -> Self:
        if not isinstance(timeout_seconds, int):
            raise Exception("invalid type")
        self._timeout_seconds = deepcopy(timeout_seconds)
        return self

    def owner_email(self, owner_email: str) -> Self:
        if not isinstance(owner_email, str):
            raise Exception("invalid type")
        self._owner_email = deepcopy(owner_email)
        return self

    # Name of the workflow to execute when this workflow fails.
    # Failure workflows can be used for handling compensation logic
    def failure_workflow(self, failure_workflow: str) -> Self:
        if not isinstance(failure_workflow, str):
            raise Exception("invalid type")
        self._failure_workflow = deepcopy(failure_workflow)
        return self

    # If the workflow can be restarted after it has reached terminal state.
    # Set this to false if restarting workflow can have side effects
    def restartable(self, restartable: bool) -> Self:
        if not isinstance(restartable, bool):
            raise Exception("invalid type")
        self._restartable = deepcopy(restartable)
        return self

    def enable_status_listener(self, sink_name: bool) -> Self:
        self._workflow_status_listener_sink = sink_name
        self._workflow_status_listener_enabled = True

    def disable_status_listener(self) -> Self:
        self._workflow_status_listener_sink = None
        self._workflow_status_listener_enabled = False

    # Workflow output follows similar structure as task input
    # See https://conductor.netflix.com/how-tos/Tasks/task-inputs.html for more details
    def output_parameters(self, output_parameters: Dict[str, Any]) -> Self:
        if output_parameters == None:
            self._output_parameters = {}
            return
        if not isinstance(output_parameters, dict):
            raise Exception("invalid type")
        for key in output_parameters.keys():
            if not isinstance(key, str):
                raise Exception("invalid type")
        self._output_parameters = deepcopy(output_parameters)
        return self

    def output_parameter(self, key: str, value: Any) -> Self:
        if self._output_parameters is None:
            self._output_parameters = {}

        self._output_parameters[key] = value
        return self

    # InputTemplate template input to the workflow.  Can have combination of variables (e.g. ${workflow.input.abc}) and static values
    def input_template(self, input_template: Dict[str, Any]) -> Self:
        if input_template == None:
            self._input_template = {}
            return
        if not isinstance(input_template, dict):
            raise Exception("invalid type")
        for key in input_template.keys():
            if not isinstance(key, str):
                raise Exception("invalid type")
        self._input_template = deepcopy(input_template)
        return self

    # Variables are set using SET_VARIABLE task. Excellent way to maintain business state
    # e.g. Variables can maintain business/user specific states which can be queried and inspected to find out the state of the workflow
    def variables(self, variables: Dict[str, Any]) -> Self:
        if variables == None:
            self._variables = {}
            return
        if not isinstance(variables, dict):
            raise Exception("invalid type")
        for key in variables.keys():
            if not isinstance(key, str):
                raise Exception("invalid type")
        self._variables = deepcopy(variables)
        return self

    # List of the input parameters to the workflow. Usage: documentation ONLY
    def input_parameters(self, input_parameters: List[str]) -> Self:
        if isinstance(input_parameters, dict) or isinstance(input_parameters, Dict):
            self._input_template = input_parameters
            return self
        if not isinstance(input_parameters, list):
            raise Exception("invalid type")
        for input_parameter in input_parameters:
            if not isinstance(input_parameter, str):
                raise Exception("invalid type")
        self._input_parameters = deepcopy(input_parameters)
        return self

    def workflow_input(self, input: dict) -> Self:
        keys = list(input.keys())
        self.input_template(input)
        return self
        
    def load(self, json_file_path: str) -> None:
        import json
        from pathlib import Path

        # Load the JSON file
        json_path = Path(json_file_path)
        if not json_path.is_file():
            raise FileNotFoundError(f"The file {json_file_path} does not exist.")

        with open(json_path, 'r') as file:
            data = json.load(file)
        workflow_def = to_workflow_def(json_data=data)
        self.name = workflow_def.name
        self._tasks = []
        for task in workflow_def.tasks:            
            if task.type == TaskType.SWITCH:                     
                switch_task = SwitchTask(task_ref_name=task.task_reference_name, case_expression=task.input_parameters.get('switchCaseValue'))
                if "default" in task.to_dict():
                    default_tasks = []
                    for default_task in task.to_dict().pop("default"):
                        default_tasks.append(simple_task(task_def_name=default_task.name, task_reference_name=default_task.task_reference_name, inputs=default_task.input_parameters))
                    switch_task.default_case(default_tasks)

                for key, value in task.to_dict()["decision_cases"].items():
                    case_tasks = []
                    for case_task in value:
                        case_tasks.append(simple_task(task_def_name=case_task.name, task_reference_name=case_task.task_reference_name, inputs=case_task.input_parameters))
                    switch_task.switch_case(key, case_tasks)
                    self._tasks.append(switch_task)

            elif task.type == TaskType.DO_WHILE:
                loop_over_tasks = []
                for loop_task in task.loop_over:
                    if not loop_task.input_parameters:
                        loop_task.input_parameters = {}

                    loop_over_tasks.append(simple_task(task_def_name=loop_task.name, task_reference_name=loop_task.task_reference_name, inputs=loop_task.input_parameters))
                self._tasks.append(DoWhileTask(task_ref_name=task.task_reference_name, termination_condition=task.loop_condition, tasks=loop_over_tasks))
            else:
                if not task.input_parameters:
                    task.input_parameters = {}
                self._tasks.append(simple_task(task_def_name=task.name, task_reference_name=task.task_reference_name, inputs=task.input_parameters))
        self._input_parameters = workflow_def.input_parameters
        self._output_parameters = workflow_def.output_parameters
        self._failure_workflow = workflow_def.failure_workflow
        self._timeout_seconds = workflow_def.timeout_seconds
        self._variables = workflow_def.variables
        self._input_template = workflow_def.input_template
        self._workflow_status_listener_enabled = workflow_def.workflow_status_listener_enabled
        self._owner_email = workflow_def.owner_email
        
    

    # Register the workflow definition with the server. If overwrite is set, the definition on the server will be
    # overwritten. When not set, the call fails if there is any change in the workflow definition between the server
    # and what is being registered.
    def register(self, overwrite: bool):
        return self._executor.register_workflow(
            overwrite=overwrite,
            workflow=self.to_workflow_def(),
        )

    def start_workflow(self, start_workflow_request: StartWorkflowRequest) -> str:
        """
        Executes the workflow inline without registering with the server.  Useful for one-off workflows that need not be registered.
        Parameters
        ----------
        start_workflow_request

        Returns
        -------
        Workflow Execution Id
        """
        start_workflow_request.workflow_def = self.to_workflow_def()
        start_workflow_request.name = self.name
        start_workflow_request.version = self.version
        return self._executor.start_workflow(start_workflow_request)

    def start_workflow_with_input(
        self,
        workflow_input: dict = {},
        correlation_id=None,
        task_to_domain=None,
        priority=None,
        idempotency_key: str = None,
        idempotency_strategy: IdempotencyStrategy = IdempotencyStrategy.FAIL, workers=None
    ) -> str:
        """
        Starts the workflow with given inputs and parameters and returns the id of the started workflow
        """

        start_workflow_request = StartWorkflowRequest()
        start_workflow_request.workflow_def = self.to_workflow_def()
        start_workflow_request.name = self.name
        start_workflow_request.version = self.version
        start_workflow_request.input = workflow_input
        start_workflow_request.correlation_id = correlation_id
        start_workflow_request.idempotency_key = idempotency_key
        start_workflow_request.idempotency_strategy = idempotency_strategy
        start_workflow_request.priority = priority
        start_workflow_request.task_to_domain = task_to_domain
        
        return self._executor.start_workflow(start_workflow_request, workers)
    

    def get_workflow(self, workflow_id: str, include_tasks: bool = None) -> Workflow:
        return self._executor.get_workflow(workflow_id, include_tasks)

    def execute(
        self,
        workflow_input: Any = {},
        wait_until_task_ref: str = "",
        wait_for_seconds: int = 10,
        request_id: str = None,
        idempotency_key: str = None,
        idempotency_strategy: IdempotencyStrategy = IdempotencyStrategy.FAIL,
        task_to_domain: dict[str, str] = None,
    ) -> WorkflowRun:
        """
        Executes a workflow synchronously.  Useful for short duration workflow (e.g. < 20 seconds)
        Parameters
        ----------
        workflow_input Input to the workflow
        wait_until_task_ref wait reference name of the task to wait until before returning the workflow results
        wait_for_seconds amount of time to wait in seconds before returning.
        request_id User supplied unique id that represents this workflow run
        Returns
        -------
        Workflow execution run.  check the status field to identify if the workflow was completed or still running
        when the call completed.
        """
        request = StartWorkflowRequest()
        request.workflow_def = self.to_workflow_def()
        request.input = workflow_input
        request.name = request.workflow_def.name
        request.version = 1
        if idempotency_key is not None:
            request.idempotency_key = idempotency_key
            request.idempotency_strategy = idempotency_strategy
        if task_to_domain is not None:
            request.task_to_domain = task_to_domain
        run = self._executor.execute_workflow(
            request,
            wait_until_task_ref=wait_until_task_ref,
            wait_for_seconds=wait_for_seconds,
            request_id=request_id,
        )

        return run

    def to_workflow_def(self) -> WorkflowDef:
        return WorkflowDef(
            name=self._name,
            description=self._description,
            version=self._version,
            tasks=self.__get_workflow_task_list(),
            input_parameters=self._input_parameters,
            output_parameters=self._output_parameters,
            failure_workflow=self._failure_workflow,
            schema_version=ConductorWorkflow.SCHEMA_VERSION,
            owner_email=self._owner_email,
            timeout_policy=self._timeout_policy,
            timeout_seconds=self._timeout_seconds,
            variables=self._variables,
            input_template=self._input_template,
            workflow_status_listener_enabled=self._workflow_status_listener_enabled,
            workflow_status_listener_sink=self._workflow_status_listener_sink,
        )

    def to_workflow_task(self):
        sub_workflow_task = InlineSubWorkflowTask(
            task_ref_name=self.name + "_" + str(uuid()), workflow=self
        )
        sub_workflow_task.input_parameters.update(self._input_template)
        return sub_workflow_task.to_workflow_task()

    def __get_workflow_task_list(self) -> List[WorkflowTask]:
        workflow_task_list = []
        for task in self._tasks:
            converted_task = task.to_workflow_task()
            # print (converted_task)
            if isinstance(converted_task, list):
                for subtask in converted_task:
                    workflow_task_list.append(subtask)
            else:
                workflow_task_list.append(converted_task)
        updated_task_list = []
        for i in range(len(workflow_task_list)):
            wft: WorkflowTask = workflow_task_list[i]
            if wft.task_definition is None:
                wft.task_definition = TaskDef()
            if container.conductor_config.debug:
                wft.task_definition.retry_count = 0
            updated_task_list.append(wft)
            if (
                wft.type == "FORK_JOIN"
                and i < len(workflow_task_list) - 1
                and workflow_task_list[i + 1].type != "JOIN"
            ):
                join_on = list(
                    map(lambda ft: ft[len(ft) - 1].task_reference_name, wft.fork_tasks)
                )
                join = JoinTask(
                    task_ref_name="join_" + wft.task_reference_name, join_on=join_on
                )
                updated_task_list.append(join.to_workflow_task())

        return updated_task_list

    def __rshift__(
        self, task: Union[TaskInterface, List[TaskInterface], Dict[Any, TaskInterface]]
    ) -> Self:
        if isinstance(task, list):
            forked_tasks = []
            for fork_task in task:
                if isinstance(fork_task, list):
                    forked_tasks.append(fork_task)
                else:
                    forked_tasks.append([fork_task])
            self.__add_fork_join_tasks(forked_tasks)
            return self
        elif isinstance(task, dict):
            switch_task = SwitchTask(
                task_ref_name="switch",
                case_expression=self._tasks[-1].output("switch_case_value"),
            )
            if "default" in task:
                switch_task.default_case(task.pop("default"))
            for key, value in task.items():
                switch_task.switch_case(key, value)

            return self.__add_task(switch_task)

        elif isinstance(task, ConductorWorkflow):
            # inline = InlineSubWorkflowTask(
            #     task_ref_name=task.name + "_" + str(uuid()), workflow=task
            # )
            # inline.input_parameters.update(task._input_template)
            # return self.__add_task(inline)
            sub_workflow_tasks = task._tasks
            for sub_task in sub_workflow_tasks:
                self.__add_task(sub_task)
            return self

        elif isinstance(task, TaskInterface):
            return self.__add_task(task)

        else:
            raise ValueError(f"Invalid task type {type(task)}")

    # Append task
    def add(self, task: Union[TaskInterface, List[TaskInterface]]) -> Self:
        if isinstance(task, list):
            for t in task:
                self.__add_task(t)
            return self
        return self.__add_task(task)

    def __add_task(self, task: TaskInterface) -> Self:
        if not (
            issubclass(type(task), TaskInterface) or isinstance(task, ConductorWorkflow)
        ):
            raise Exception(
                f"invalid task -- if using @worker_task or @WorkerTask decorator ensure task_ref_name is passed as "
                f"argument.  task is {type(task)}"
            )
        self._tasks.append(deepcopy(task))
        return self

    def __add_fork_join_tasks(self, forked_tasks: List[List[TaskInterface]]) -> Self:
        for single_fork in forked_tasks:
            for task in single_fork:
                if not (
                    issubclass(type(task), TaskInterface)
                    or isinstance(task, ConductorWorkflow)
                ):
                    raise Exception("invalid type")

        suffix = str(uuid())

        fork_task = ForkTask(
            task_ref_name="forked_" + suffix,
            forked_tasks=forked_tasks,
            join_on=[
                each.task_reference_name for each in itertools.chain(*forked_tasks)
            ],
        )
        self._tasks.append(fork_task)
        return self

    def __call__(self, **kwargs) -> WorkflowRun:
        input = {}
        if kwargs is not None and len(kwargs) > 0:
            input = kwargs
        return self.execute(workflow_input=input)

    def input(self, json_path: str) -> str:
        if json_path is None:
            return "${" + f"workflow.input" + "}"
        else:
            return "${" + f"workflow.input.{json_path}" + "}"

    def output(self, json_path: str = None) -> str:
        if json_path is None:
            return "${" + f"workflow.output" + "}"
        else:
            return "${" + f"workflow.output.{json_path}" + "}"

    def stop_all_running_workflows(self):
        try:
            running_workflows = workflow_client.search(query="status IN (RUNNING)")
            if running_workflows:
                for workflow in running_workflows.results:
                    if workflow.workflow_type == self.name:
                        workflow_client.terminate_workflow(
                            workflow_id=workflow.workflow_id
                        )
                logging.info("Stopped all running workflows")
            else:
                logging.info("No running workflows found")
        except Exception as e:
            logging.error(f"Error while stopping running workflows: {e}")


class InlineSubWorkflowTask(TaskInterface):
    def __init__(self, task_ref_name: str, workflow: ConductorWorkflow) -> Self:
        super().__init__(
            task_reference_name=task_ref_name,
            task_type=TaskType.SUB_WORKFLOW,
        )
        self._workflow = deepcopy(workflow)
        self._workflow_name = deepcopy(workflow.name)
        self._workflow_version = deepcopy(workflow.version)
        self._workflow_definition = deepcopy(workflow.to_workflow_def())

    def to_workflow_task(self) -> WorkflowTask:
        workflow = super().to_workflow_task()
        workflow.sub_workflow_param = SubWorkflowParams(
            name=self._workflow_name,
            version=self._workflow_version,
            workflow_definition=self._workflow_definition,
        )
        return workflow
