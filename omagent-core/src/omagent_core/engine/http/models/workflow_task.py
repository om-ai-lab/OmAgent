import pprint
import re  # noqa: F401
from typing import List

import six
from omagent_core.engine.http.models.state_change_event import (
    StateChangeConfig, StateChangeEvent, StateChangeEventType)


class CacheConfig(object):
    swagger_types = {"key": "str", "ttl_in_second": "int"}

    attribute_map = {"key": "key", "ttl_in_second": "ttlInSecond"}

    def __init__(self, key: str, ttl_in_second: int):
        self._key = key
        self._ttl_in_second = ttl_in_second

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, key):
        self._key = key

    @property
    def ttl_in_second(self):
        return self._ttl_in_second

    @ttl_in_second.setter
    def ttl_in_second(self, ttl_in_second):
        self._ttl_in_second = ttl_in_second


class WorkflowTask(object):
    """
    Attributes:
      swagger_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """

    swagger_types = {
        "name": "str",
        "task_reference_name": "str",
        "description": "str",
        "input_parameters": "dict(str, object)",
        "type": "str",
        "dynamic_task_name_param": "str",
        "case_value_param": "str",
        "case_expression": "str",
        "script_expression": "str",
        "decision_cases": "dict(str, list[WorkflowTask])",
        "dynamic_fork_join_tasks_param": "str",
        "dynamic_fork_tasks_param": "str",
        "dynamic_fork_tasks_input_param_name": "str",
        "default_case": "list[WorkflowTask]",
        "fork_tasks": "list[list[WorkflowTask]]",
        "start_delay": "int",
        "sub_workflow_param": "SubWorkflowParams",
        "join_on": "list[str]",
        "sink": "str",
        "optional": "bool",
        "task_definition": "TaskDef",
        "rate_limited": "bool",
        "default_exclusive_join_task": "list[str]",
        "async_complete": "bool",
        "loop_condition": "str",
        "loop_over": "list[WorkflowTask]",
        "retry_count": "int",
        "evaluator_type": "str",
        "expression": "str",
        "workflow_task_type": "str",
        "on_state_change": "dict(str, StateChangeConfig)",
        "cache_config": "CacheConfig",
    }

    attribute_map = {
        "name": "name",
        "task_reference_name": "taskReferenceName",
        "description": "description",
        "input_parameters": "inputParameters",
        "type": "type",
        "dynamic_task_name_param": "dynamicTaskNameParam",
        "case_value_param": "caseValueParam",
        "case_expression": "caseExpression",
        "script_expression": "scriptExpression",
        "decision_cases": "decisionCases",
        "dynamic_fork_join_tasks_param": "dynamicForkTasksParam",
        "dynamic_fork_tasks_param": "dynamicForkTasksParam",
        "dynamic_fork_tasks_input_param_name": "dynamicForkTasksInputParamName",
        "default_case": "defaultCase",
        "fork_tasks": "forkTasks",
        "start_delay": "startDelay",
        "sub_workflow_param": "subWorkflowParam",
        "join_on": "joinOn",
        "sink": "sink",
        "optional": "optional",
        "task_definition": "taskDefinition",
        "rate_limited": "rateLimited",
        "default_exclusive_join_task": "defaultExclusiveJoinTask",
        "async_complete": "asyncComplete",
        "loop_condition": "loopCondition",
        "loop_over": "loopOver",
        "retry_count": "retryCount",
        "evaluator_type": "evaluatorType",
        "expression": "expression",
        "workflow_task_type": "workflowTaskType",
        "on_state_change": "onStateChange",
        "cache_config": "cacheConfig",
    }

    def __init__(
        self,
        name=None,
        task_reference_name=None,
        description=None,
        input_parameters=None,
        type=None,
        dynamic_task_name_param=None,
        case_value_param=None,
        case_expression=None,
        script_expression=None,
        decision_cases=None,
        dynamic_fork_join_tasks_param=None,
        dynamic_fork_tasks_param=None,
        dynamic_fork_tasks_input_param_name=None,
        default_case=None,
        fork_tasks=None,
        start_delay=None,
        sub_workflow_param=None,
        join_on=None,
        sink=None,
        optional=None,
        task_definition=None,
        rate_limited=None,
        default_exclusive_join_task=None,
        async_complete=None,
        loop_condition=None,
        loop_over=None,
        retry_count=None,
        evaluator_type=None,
        expression=None,
        workflow_task_type=None,
        on_state_change: dict[str, StateChangeConfig] = None,
        cache_config: CacheConfig = None,
    ):  # noqa: E501
        """WorkflowTask - a model defined in Swagger"""  # noqa: E501
        self._name = None
        self._task_reference_name = None
        self._description = None
        self._input_parameters = None
        self._type = None
        self._dynamic_task_name_param = None
        self._case_value_param = None
        self._case_expression = None
        self._script_expression = None
        self._decision_cases = None
        self._dynamic_fork_join_tasks_param = None
        self._dynamic_fork_tasks_param = None
        self._dynamic_fork_tasks_input_param_name = None
        self._default_case = None
        self._fork_tasks = None
        self._start_delay = None
        self._sub_workflow_param = None
        self._join_on = None
        self._sink = None
        self._optional = None
        self._task_definition = None
        self._rate_limited = None
        self._default_exclusive_join_task = None
        self._async_complete = None
        self._loop_condition = None
        self._loop_over = None
        self._retry_count = None
        self._evaluator_type = None
        self._expression = None
        self._workflow_task_type = None
        self.discriminator = None
        self._on_state_change = None
        self._cache_config = None
        self.name = name
        self.task_reference_name = task_reference_name
        if description is not None:
            self.description = description
        if input_parameters is not None:
            self.input_parameters = input_parameters
        if type is not None:
            self.type = type
        if dynamic_task_name_param is not None:
            self.dynamic_task_name_param = dynamic_task_name_param
        if case_value_param is not None:
            self.case_value_param = case_value_param
        if case_expression is not None:
            self.case_expression = case_expression
        if script_expression is not None:
            self.script_expression = script_expression
        if decision_cases is not None:
            self.decision_cases = decision_cases
        if dynamic_fork_join_tasks_param is not None:
            self.dynamic_fork_join_tasks_param = dynamic_fork_join_tasks_param
        if dynamic_fork_tasks_param is not None:
            self.dynamic_fork_tasks_param = dynamic_fork_tasks_param
        if dynamic_fork_tasks_input_param_name is not None:
            self.dynamic_fork_tasks_input_param_name = (
                dynamic_fork_tasks_input_param_name
            )
        if default_case is not None:
            self.default_case = default_case
        if fork_tasks is not None:
            self.fork_tasks = fork_tasks
        if start_delay is not None:
            self.start_delay = start_delay
        if sub_workflow_param is not None:
            self.sub_workflow_param = sub_workflow_param
        if join_on is not None:
            self.join_on = join_on
        if sink is not None:
            self.sink = sink
        if optional is not None:
            self.optional = optional
        if task_definition is not None:
            self.task_definition = task_definition
        if rate_limited is not None:
            self.rate_limited = rate_limited
        if default_exclusive_join_task is not None:
            self.default_exclusive_join_task = default_exclusive_join_task
        if async_complete is not None:
            self.async_complete = async_complete
        if loop_condition is not None:
            self.loop_condition = loop_condition
        if loop_over is not None:
            self.loop_over = loop_over
        if retry_count is not None:
            self.retry_count = retry_count
        if evaluator_type is not None:
            self.evaluator_type = evaluator_type
        if expression is not None:
            self.expression = expression
        if workflow_task_type is not None:
            self.workflow_task_type = workflow_task_type
        if on_state_change is not None:
            self._on_state_change = on_state_change
        self._cache_config = cache_config

    @property
    def name(self):
        """Gets the name of this WorkflowTask.  # noqa: E501


        :return: The name of this WorkflowTask.  # noqa: E501
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name of this WorkflowTask.


        :param name: The name of this WorkflowTask.  # noqa: E501
        :type: str
        """
        self._name = name

    @property
    def task_reference_name(self):
        """Gets the task_reference_name of this WorkflowTask.  # noqa: E501


        :return: The task_reference_name of this WorkflowTask.  # noqa: E501
        :rtype: str
        """
        return self._task_reference_name

    @task_reference_name.setter
    def task_reference_name(self, task_reference_name):
        """Sets the task_reference_name of this WorkflowTask.


        :param task_reference_name: The task_reference_name of this WorkflowTask.  # noqa: E501
        :type: str
        """
        self._task_reference_name = task_reference_name

    @property
    def description(self):
        """Gets the description of this WorkflowTask.  # noqa: E501


        :return: The description of this WorkflowTask.  # noqa: E501
        :rtype: str
        """
        return self._description

    @description.setter
    def description(self, description):
        """Sets the description of this WorkflowTask.


        :param description: The description of this WorkflowTask.  # noqa: E501
        :type: str
        """

        self._description = description

    @property
    def input_parameters(self):
        """Gets the input_parameters of this WorkflowTask.  # noqa: E501


        :return: The input_parameters of this WorkflowTask.  # noqa: E501
        :rtype: dict(str, object)
        """
        return self._input_parameters

    @input_parameters.setter
    def input_parameters(self, input_parameters):
        """Sets the input_parameters of this WorkflowTask.


        :param input_parameters: The input_parameters of this WorkflowTask.  # noqa: E501
        :type: dict(str, object)
        """

        self._input_parameters = input_parameters

    @property
    def type(self):
        """Gets the type of this WorkflowTask.  # noqa: E501


        :return: The type of this WorkflowTask.  # noqa: E501
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type):
        """Sets the type of this WorkflowTask.


        :param type: The type of this WorkflowTask.  # noqa: E501
        :type: str
        """

        self._type = type

    @property
    def dynamic_task_name_param(self):
        """Gets the dynamic_task_name_param of this WorkflowTask.  # noqa: E501


        :return: The dynamic_task_name_param of this WorkflowTask.  # noqa: E501
        :rtype: str
        """
        return self._dynamic_task_name_param

    @dynamic_task_name_param.setter
    def dynamic_task_name_param(self, dynamic_task_name_param):
        """Sets the dynamic_task_name_param of this WorkflowTask.


        :param dynamic_task_name_param: The dynamic_task_name_param of this WorkflowTask.  # noqa: E501
        :type: str
        """

        self._dynamic_task_name_param = dynamic_task_name_param

    @property
    def case_value_param(self):
        """Gets the case_value_param of this WorkflowTask.  # noqa: E501


        :return: The case_value_param of this WorkflowTask.  # noqa: E501
        :rtype: str
        """
        return self._case_value_param

    @case_value_param.setter
    def case_value_param(self, case_value_param):
        """Sets the case_value_param of this WorkflowTask.


        :param case_value_param: The case_value_param of this WorkflowTask.  # noqa: E501
        :type: str
        """

        self._case_value_param = case_value_param

    @property
    def case_expression(self):
        """Gets the case_expression of this WorkflowTask.  # noqa: E501


        :return: The case_expression of this WorkflowTask.  # noqa: E501
        :rtype: str
        """
        return self._case_expression

    @case_expression.setter
    def case_expression(self, case_expression):
        """Sets the case_expression of this WorkflowTask.


        :param case_expression: The case_expression of this WorkflowTask.  # noqa: E501
        :type: str
        """

        self._case_expression = case_expression

    @property
    def script_expression(self):
        """Gets the script_expression of this WorkflowTask.  # noqa: E501


        :return: The script_expression of this WorkflowTask.  # noqa: E501
        :rtype: str
        """
        return self._script_expression

    @script_expression.setter
    def script_expression(self, script_expression):
        """Sets the script_expression of this WorkflowTask.


        :param script_expression: The script_expression of this WorkflowTask.  # noqa: E501
        :type: str
        """

        self._script_expression = script_expression

    @property
    def decision_cases(self):
        """Gets the decision_cases of this WorkflowTask.  # noqa: E501


        :return: The decision_cases of this WorkflowTask.  # noqa: E501
        :rtype: dict(str, list[WorkflowTask])
        """
        return self._decision_cases

    @decision_cases.setter
    def decision_cases(self, decision_cases):
        """Sets the decision_cases of this WorkflowTask.


        :param decision_cases: The decision_cases of this WorkflowTask.  # noqa: E501
        :type: dict(str, list[WorkflowTask])
        """

        self._decision_cases = decision_cases

    @property
    def dynamic_fork_join_tasks_param(self):
        """Gets the dynamic_fork_join_tasks_param of this WorkflowTask.  # noqa: E501


        :return: The dynamic_fork_join_tasks_param of this WorkflowTask.  # noqa: E501
        :rtype: str
        """
        return self._dynamic_fork_join_tasks_param

    @dynamic_fork_join_tasks_param.setter
    def dynamic_fork_join_tasks_param(self, dynamic_fork_join_tasks_param):
        """Sets the dynamic_fork_join_tasks_param of this WorkflowTask.


        :param dynamic_fork_join_tasks_param: The dynamic_fork_join_tasks_param of this WorkflowTask.  # noqa: E501
        :type: str
        """

        self._dynamic_fork_join_tasks_param = dynamic_fork_join_tasks_param

    @property
    def dynamic_fork_tasks_param(self):
        """Gets the dynamic_fork_tasks_param of this WorkflowTask.  # noqa: E501


        :return: The dynamic_fork_tasks_param of this WorkflowTask.  # noqa: E501
        :rtype: str
        """
        return self._dynamic_fork_tasks_param

    @dynamic_fork_tasks_param.setter
    def dynamic_fork_tasks_param(self, dynamic_fork_tasks_param):
        """Sets the dynamic_fork_tasks_param of this WorkflowTask.


        :param dynamic_fork_tasks_param: The dynamic_fork_tasks_param of this WorkflowTask.  # noqa: E501
        :type: str
        """

        self._dynamic_fork_tasks_param = dynamic_fork_tasks_param

    @property
    def dynamic_fork_tasks_input_param_name(self):
        """Gets the dynamic_fork_tasks_input_param_name of this WorkflowTask.  # noqa: E501


        :return: The dynamic_fork_tasks_input_param_name of this WorkflowTask.  # noqa: E501
        :rtype: str
        """
        return self._dynamic_fork_tasks_input_param_name

    @dynamic_fork_tasks_input_param_name.setter
    def dynamic_fork_tasks_input_param_name(self, dynamic_fork_tasks_input_param_name):
        """Sets the dynamic_fork_tasks_input_param_name of this WorkflowTask.


        :param dynamic_fork_tasks_input_param_name: The dynamic_fork_tasks_input_param_name of this WorkflowTask.  # noqa: E501
        :type: str
        """

        self._dynamic_fork_tasks_input_param_name = dynamic_fork_tasks_input_param_name

    @property
    def default_case(self):
        """Gets the default_case of this WorkflowTask.  # noqa: E501


        :return: The default_case of this WorkflowTask.  # noqa: E501
        :rtype: list[WorkflowTask]
        """
        return self._default_case

    @default_case.setter
    def default_case(self, default_case):
        """Sets the default_case of this WorkflowTask.


        :param default_case: The default_case of this WorkflowTask.  # noqa: E501
        :type: list[WorkflowTask]
        """

        self._default_case = default_case

    @property
    def fork_tasks(self):
        """Gets the fork_tasks of this WorkflowTask.  # noqa: E501


        :return: The fork_tasks of this WorkflowTask.  # noqa: E501
        :rtype: list[list[WorkflowTask]]
        """
        return self._fork_tasks

    @fork_tasks.setter
    def fork_tasks(self, fork_tasks):
        """Sets the fork_tasks of this WorkflowTask.


        :param fork_tasks: The fork_tasks of this WorkflowTask.  # noqa: E501
        :type: list[list[WorkflowTask]]
        """

        self._fork_tasks = fork_tasks

    @property
    def start_delay(self):
        """Gets the start_delay of this WorkflowTask.  # noqa: E501


        :return: The start_delay of this WorkflowTask.  # noqa: E501
        :rtype: int
        """
        return self._start_delay

    @start_delay.setter
    def start_delay(self, start_delay):
        """Sets the start_delay of this WorkflowTask.


        :param start_delay: The start_delay of this WorkflowTask.  # noqa: E501
        :type: int
        """

        self._start_delay = start_delay

    @property
    def sub_workflow_param(self):
        """Gets the sub_workflow_param of this WorkflowTask.  # noqa: E501


        :return: The sub_workflow_param of this WorkflowTask.  # noqa: E501
        :rtype: SubWorkflowParams
        """
        return self._sub_workflow_param

    @sub_workflow_param.setter
    def sub_workflow_param(self, sub_workflow_param):
        """Sets the sub_workflow_param of this WorkflowTask.


        :param sub_workflow_param: The sub_workflow_param of this WorkflowTask.  # noqa: E501
        :type: SubWorkflowParams
        """

        self._sub_workflow_param = sub_workflow_param

    @property
    def join_on(self):
        """Gets the join_on of this WorkflowTask.  # noqa: E501


        :return: The join_on of this WorkflowTask.  # noqa: E501
        :rtype: list[str]
        """
        return self._join_on

    @join_on.setter
    def join_on(self, join_on):
        """Sets the join_on of this WorkflowTask.


        :param join_on: The join_on of this WorkflowTask.  # noqa: E501
        :type: list[str]
        """

        self._join_on = join_on

    @property
    def sink(self):
        """Gets the sink of this WorkflowTask.  # noqa: E501


        :return: The sink of this WorkflowTask.  # noqa: E501
        :rtype: str
        """
        return self._sink

    @sink.setter
    def sink(self, sink):
        """Sets the sink of this WorkflowTask.


        :param sink: The sink of this WorkflowTask.  # noqa: E501
        :type: str
        """

        self._sink = sink

    @property
    def optional(self):
        """Gets the optional of this WorkflowTask.  # noqa: E501


        :return: The optional of this WorkflowTask.  # noqa: E501
        :rtype: bool
        """
        return self._optional

    @optional.setter
    def optional(self, optional):
        """Sets the optional of this WorkflowTask.


        :param optional: The optional of this WorkflowTask.  # noqa: E501
        :type: bool
        """

        self._optional = optional

    @property
    def task_definition(self):
        """Gets the task_definition of this WorkflowTask.  # noqa: E501


        :return: The task_definition of this WorkflowTask.  # noqa: E501
        :rtype: TaskDef
        """
        return self._task_definition

    @task_definition.setter
    def task_definition(self, task_definition):
        """Sets the task_definition of this WorkflowTask.


        :param task_definition: The task_definition of this WorkflowTask.  # noqa: E501
        :type: TaskDef
        """

        self._task_definition = task_definition

    @property
    def rate_limited(self):
        """Gets the rate_limited of this WorkflowTask.  # noqa: E501


        :return: The rate_limited of this WorkflowTask.  # noqa: E501
        :rtype: bool
        """
        return self._rate_limited

    @rate_limited.setter
    def rate_limited(self, rate_limited):
        """Sets the rate_limited of this WorkflowTask.


        :param rate_limited: The rate_limited of this WorkflowTask.  # noqa: E501
        :type: bool
        """

        self._rate_limited = rate_limited

    @property
    def default_exclusive_join_task(self):
        """Gets the default_exclusive_join_task of this WorkflowTask.  # noqa: E501


        :return: The default_exclusive_join_task of this WorkflowTask.  # noqa: E501
        :rtype: list[str]
        """
        return self._default_exclusive_join_task

    @default_exclusive_join_task.setter
    def default_exclusive_join_task(self, default_exclusive_join_task):
        """Sets the default_exclusive_join_task of this WorkflowTask.


        :param default_exclusive_join_task: The default_exclusive_join_task of this WorkflowTask.  # noqa: E501
        :type: list[str]
        """

        self._default_exclusive_join_task = default_exclusive_join_task

    @property
    def async_complete(self):
        """Gets the async_complete of this WorkflowTask.  # noqa: E501


        :return: The async_complete of this WorkflowTask.  # noqa: E501
        :rtype: bool
        """
        return self._async_complete

    @async_complete.setter
    def async_complete(self, async_complete):
        """Sets the async_complete of this WorkflowTask.


        :param async_complete: The async_complete of this WorkflowTask.  # noqa: E501
        :type: bool
        """

        self._async_complete = async_complete

    @property
    def loop_condition(self):
        """Gets the loop_condition of this WorkflowTask.  # noqa: E501


        :return: The loop_condition of this WorkflowTask.  # noqa: E501
        :rtype: str
        """
        return self._loop_condition

    @loop_condition.setter
    def loop_condition(self, loop_condition):
        """Sets the loop_condition of this WorkflowTask.


        :param loop_condition: The loop_condition of this WorkflowTask.  # noqa: E501
        :type: str
        """

        self._loop_condition = loop_condition

    @property
    def loop_over(self):
        """Gets the loop_over of this WorkflowTask.  # noqa: E501


        :return: The loop_over of this WorkflowTask.  # noqa: E501
        :rtype: list[WorkflowTask]
        """
        return self._loop_over

    @loop_over.setter
    def loop_over(self, loop_over):
        """Sets the loop_over of this WorkflowTask.


        :param loop_over: The loop_over of this WorkflowTask.  # noqa: E501
        :type: list[WorkflowTask]
        """

        self._loop_over = loop_over

    @property
    def retry_count(self):
        """Gets the retry_count of this WorkflowTask.  # noqa: E501


        :return: The retry_count of this WorkflowTask.  # noqa: E501
        :rtype: int
        """
        return self._retry_count

    @retry_count.setter
    def retry_count(self, retry_count):
        """Sets the retry_count of this WorkflowTask.


        :param retry_count: The retry_count of this WorkflowTask.  # noqa: E501
        :type: int
        """

        self._retry_count = retry_count

    @property
    def evaluator_type(self):
        """Gets the evaluator_type of this WorkflowTask.  # noqa: E501


        :return: The evaluator_type of this WorkflowTask.  # noqa: E501
        :rtype: str
        """
        return self._evaluator_type

    @evaluator_type.setter
    def evaluator_type(self, evaluator_type):
        """Sets the evaluator_type of this WorkflowTask.


        :param evaluator_type: The evaluator_type of this WorkflowTask.  # noqa: E501
        :type: str
        """

        self._evaluator_type = evaluator_type

    @property
    def expression(self):
        """Gets the expression of this WorkflowTask.  # noqa: E501


        :return: The expression of this WorkflowTask.  # noqa: E501
        :rtype: str
        """
        return self._expression

    @expression.setter
    def expression(self, expression):
        """Sets the expression of this WorkflowTask.


        :param expression: The expression of this WorkflowTask.  # noqa: E501
        :type: str
        """

        self._expression = expression

    @property
    def workflow_task_type(self):
        """Gets the workflow_task_type of this WorkflowTask.  # noqa: E501


        :return: The workflow_task_type of this WorkflowTask.  # noqa: E501
        :rtype: str
        """
        return self._workflow_task_type

    @workflow_task_type.setter
    def workflow_task_type(self, workflow_task_type):
        """Sets the workflow_task_type of this WorkflowTask.


        :param workflow_task_type: The workflow_task_type of this WorkflowTask.  # noqa: E501
        :type: str
        """
        self._workflow_task_type = workflow_task_type

    @property
    def on_state_change(self) -> dict[str, List[StateChangeEvent]]:
        return self._on_state_change

    @on_state_change.setter
    def on_state_change(self, state_change: StateChangeConfig):
        self._on_state_change = {state_change.type: state_change.events}

    @property
    def cache_config(self) -> CacheConfig:
        return self._cache_config

    @cache_config.setter
    def cache_config(self, cache_config: CacheConfig):
        self._cache_config = cache_config

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.swagger_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(
                    map(lambda x: x.to_dict() if hasattr(x, "to_dict") else x, value)
                )
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(
                    map(
                        lambda item: (
                            (item[0], item[1].to_dict())
                            if hasattr(item[1], "to_dict")
                            else item
                        ),
                        value.items(),
                    )
                )
            else:
                result[attr] = value
        if issubclass(WorkflowTask, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, WorkflowTask):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
