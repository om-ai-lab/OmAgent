import json
import pprint
import re  # noqa: F401
from typing import List

import six
from omagent_core.engine.helpers.helper import ObjectMapper
from omagent_core.engine.http.models.workflow_task import WorkflowTask

object_mapper = ObjectMapper()


class WorkflowDef(object):
    """
    Attributes:
      swagger_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """

    swagger_types = {
        "owner_app": "str",
        "create_time": "int",
        "update_time": "int",
        "created_by": "str",
        "updated_by": "str",
        "name": "str",
        "description": "str",
        "version": "int",
        "tasks": "list[WorkflowTask]",
        "input_parameters": "list[str]",
        "output_parameters": "dict(str, object)",
        "failure_workflow": "str",
        "schema_version": "int",
        "restartable": "bool",
        "workflow_status_listener_enabled": "bool",
        "workflow_status_listener_sink": "str",
        "owner_email": "str",
        "timeout_policy": "str",
        "timeout_seconds": "int",
        "variables": "dict(str, object)",
        "input_template": "dict(str, object)",
    }

    attribute_map = {
        "owner_app": "ownerApp",
        "create_time": "createTime",
        "update_time": "updateTime",
        "created_by": "createdBy",
        "updated_by": "updatedBy",
        "name": "name",
        "description": "description",
        "version": "version",
        "tasks": "tasks",
        "input_parameters": "inputParameters",
        "output_parameters": "outputParameters",
        "failure_workflow": "failureWorkflow",
        "schema_version": "schemaVersion",
        "restartable": "restartable",
        "workflow_status_listener_enabled": "workflowStatusListenerEnabled",
        "workflow_status_listener_sink": "workflowStatusListenerSink",
        "owner_email": "ownerEmail",
        "timeout_policy": "timeoutPolicy",
        "timeout_seconds": "timeoutSeconds",
        "variables": "variables",
        "input_template": "inputTemplate",
    }

    def __init__(
        self,
        owner_app=None,
        create_time=None,
        update_time=None,
        created_by=None,
        updated_by=None,
        name=None,
        description=None,
        version=None,
        tasks=None,
        input_parameters=None,
        output_parameters: dict = {},
        failure_workflow=None,
        schema_version=None,
        restartable=None,
        workflow_status_listener_enabled=None,
        workflow_status_listener_sink=None,
        owner_email=None,
        timeout_policy=None,
        timeout_seconds=None,
        variables=None,
        input_template=None,
    ):  # noqa: E501
        """WorkflowDef - a model defined in Swagger"""  # noqa: E501
        self._owner_app = None
        self._create_time = None
        self._update_time = None
        self._created_by = None
        self._updated_by = None
        self._name = None
        self._description = None
        self._version = None
        self._tasks = []
        self._input_parameters = None
        self._output_parameters = None
        self._failure_workflow = None
        self._schema_version = None
        self._restartable = None
        self._workflow_status_listener_enabled = None
        self._workflow_status_listener_sink = None
        self._owner_email = None
        self._timeout_policy = None
        self._timeout_seconds = None
        self._variables = None
        self._input_template = None
        self.discriminator = None
        if owner_app is not None:
            self.owner_app = owner_app
        if create_time is not None:
            self.create_time = create_time
        if update_time is not None:
            self.update_time = update_time
        if created_by is not None:
            self.created_by = created_by
        if updated_by is not None:
            self.updated_by = updated_by
        self.name = name
        if description is not None:
            self.description = description
        if version is not None:
            self.version = version
        self.tasks = tasks
        if input_parameters is not None:
            self.input_parameters = input_parameters
        if output_parameters is not None:
            self.output_parameters = output_parameters
        if failure_workflow is not None:
            self.failure_workflow = failure_workflow
        if schema_version is not None:
            self.schema_version = schema_version
        if restartable is not None:
            self.restartable = restartable
        if workflow_status_listener_enabled is not None:
            self._workflow_status_listener_enabled = workflow_status_listener_enabled
        if workflow_status_listener_sink is not None:
            self._workflow_status_listener_sink = workflow_status_listener_sink
        if owner_email is not None:
            self.owner_email = owner_email
        if timeout_policy is not None:
            self.timeout_policy = timeout_policy
        self.timeout_seconds = timeout_seconds
        if variables is not None:
            self.variables = variables
        if input_template is not None:
            self.input_template = input_template

    @property
    def owner_app(self):
        """Gets the owner_app of this WorkflowDef.  # noqa: E501


        :return: The owner_app of this WorkflowDef.  # noqa: E501
        :rtype: str
        """
        return self._owner_app

    @owner_app.setter
    def owner_app(self, owner_app):
        """Sets the owner_app of this WorkflowDef.


        :param owner_app: The owner_app of this WorkflowDef.  # noqa: E501
        :type: str
        """

        self._owner_app = owner_app

    @property
    def create_time(self):
        """Gets the create_time of this WorkflowDef.  # noqa: E501


        :return: The create_time of this WorkflowDef.  # noqa: E501
        :rtype: int
        """
        return self._create_time

    @create_time.setter
    def create_time(self, create_time):
        """Sets the create_time of this WorkflowDef.


        :param create_time: The create_time of this WorkflowDef.  # noqa: E501
        :type: int
        """

        self._create_time = create_time

    @property
    def update_time(self):
        """Gets the update_time of this WorkflowDef.  # noqa: E501


        :return: The update_time of this WorkflowDef.  # noqa: E501
        :rtype: int
        """
        return self._update_time

    @update_time.setter
    def update_time(self, update_time):
        """Sets the update_time of this WorkflowDef.


        :param update_time: The update_time of this WorkflowDef.  # noqa: E501
        :type: int
        """

        self._update_time = update_time

    @property
    def created_by(self):
        """Gets the created_by of this WorkflowDef.  # noqa: E501


        :return: The created_by of this WorkflowDef.  # noqa: E501
        :rtype: str
        """
        return self._created_by

    @created_by.setter
    def created_by(self, created_by):
        """Sets the created_by of this WorkflowDef.


        :param created_by: The created_by of this WorkflowDef.  # noqa: E501
        :type: str
        """

        self._created_by = created_by

    @property
    def updated_by(self):
        """Gets the updated_by of this WorkflowDef.  # noqa: E501


        :return: The updated_by of this WorkflowDef.  # noqa: E501
        :rtype: str
        """
        return self._updated_by

    @updated_by.setter
    def updated_by(self, updated_by):
        """Sets the updated_by of this WorkflowDef.


        :param updated_by: The updated_by of this WorkflowDef.  # noqa: E501
        :type: str
        """

        self._updated_by = updated_by

    @property
    def name(self):
        """Gets the name of this WorkflowDef.  # noqa: E501


        :return: The name of this WorkflowDef.  # noqa: E501
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name of this WorkflowDef.


        :param name: The name of this WorkflowDef.  # noqa: E501
        :type: str
        """
        self._name = name

    @property
    def description(self):
        """Gets the description of this WorkflowDef.  # noqa: E501


        :return: The description of this WorkflowDef.  # noqa: E501
        :rtype: str
        """
        return self._description

    @description.setter
    def description(self, description):
        """Sets the description of this WorkflowDef.


        :param description: The description of this WorkflowDef.  # noqa: E501
        :type: str
        """

        self._description = description

    @property
    def version(self):
        """Gets the version of this WorkflowDef.  # noqa: E501


        :return: The version of this WorkflowDef.  # noqa: E501
        :rtype: int
        """
        return self._version

    @version.setter
    def version(self, version):
        """Sets the version of this WorkflowDef.


        :param version: The version of this WorkflowDef.  # noqa: E501
        :type: int
        """

        self._version = version

    @property
    def tasks(self):
        """Gets the tasks of this WorkflowDef.  # noqa: E501


        :return: The tasks of this WorkflowDef.  # noqa: E501
        :rtype: list[WorkflowTask]
        """
        if self._tasks is None:
            self._tasks = []
        return self._tasks

    @tasks.setter
    def tasks(self, tasks: List[WorkflowTask]):
        """Sets the tasks of this WorkflowDef.


        :param tasks: The tasks of this WorkflowDef.  # noqa: E501
        :type: list[WorkflowTask]
        """
        self._tasks = tasks

    @property
    def input_parameters(self):
        """Gets the input_parameters of this WorkflowDef.  # noqa: E501


        :return: The input_parameters of this WorkflowDef.  # noqa: E501
        :rtype: list[str]
        """
        return self._input_parameters

    @input_parameters.setter
    def input_parameters(self, input_parameters):
        """Sets the input_parameters of this WorkflowDef.


        :param input_parameters: The input_parameters of this WorkflowDef.  # noqa: E501
        :type: list[str]
        """

        self._input_parameters = input_parameters

    @property
    def output_parameters(self):
        """Gets the output_parameters of this WorkflowDef.  # noqa: E501


        :return: The output_parameters of this WorkflowDef.  # noqa: E501
        :rtype: dict(str, object)
        """
        return self._output_parameters

    @output_parameters.setter
    def output_parameters(self, output_parameters):
        """Sets the output_parameters of this WorkflowDef.


        :param output_parameters: The output_parameters of this WorkflowDef.  # noqa: E501
        :type: dict(str, object)
        """

        self._output_parameters = output_parameters

    @property
    def failure_workflow(self):
        """Gets the failure_workflow of this WorkflowDef.  # noqa: E501


        :return: The failure_workflow of this WorkflowDef.  # noqa: E501
        :rtype: str
        """
        return self._failure_workflow

    @failure_workflow.setter
    def failure_workflow(self, failure_workflow):
        """Sets the failure_workflow of this WorkflowDef.


        :param failure_workflow: The failure_workflow of this WorkflowDef.  # noqa: E501
        :type: str
        """

        self._failure_workflow = failure_workflow

    @property
    def schema_version(self):
        """Gets the schema_version of this WorkflowDef.  # noqa: E501


        :return: The schema_version of this WorkflowDef.  # noqa: E501
        :rtype: int
        """
        return self._schema_version

    @schema_version.setter
    def schema_version(self, schema_version):
        """Sets the schema_version of this WorkflowDef.


        :param schema_version: The schema_version of this WorkflowDef.  # noqa: E501
        :type: int
        """

        self._schema_version = schema_version

    @property
    def restartable(self):
        """Gets the restartable of this WorkflowDef.  # noqa: E501


        :return: The restartable of this WorkflowDef.  # noqa: E501
        :rtype: bool
        """
        return self._restartable

    @restartable.setter
    def restartable(self, restartable):
        """Sets the restartable of this WorkflowDef.


        :param restartable: The restartable of this WorkflowDef.  # noqa: E501
        :type: bool
        """

        self._restartable = restartable

    @property
    def workflow_status_listener_enabled(self):
        """Gets the workflow_status_listener_enabled of this WorkflowDef.  # noqa: E501


        :return: The workflow_status_listener_enabled of this WorkflowDef.  # noqa: E501
        :rtype: bool
        """
        return self._workflow_status_listener_enabled

    @workflow_status_listener_enabled.setter
    def workflow_status_listener_enabled(self, workflow_status_listener_enabled):
        """Sets the workflow_status_listener_enabled of this WorkflowDef.


        :param workflow_status_listener_enabled: The workflow_status_listener_enabled of this WorkflowDef.  # noqa: E501
        :type: bool
        """

        self._workflow_status_listener_enabled = workflow_status_listener_enabled

    @property
    def workflow_status_listener_sink(self):
        return self._workflow_status_listener_sink

    @workflow_status_listener_sink.setter
    def workflow_status_listener_sink(self, workflow_status_listener_sink):
        self._workflow_status_listener_sink = workflow_status_listener_sink

    @property
    def owner_email(self):
        """Gets the owner_email of this WorkflowDef.  # noqa: E501


        :return: The owner_email of this WorkflowDef.  # noqa: E501
        :rtype: str
        """
        return self._owner_email

    @owner_email.setter
    def owner_email(self, owner_email):
        """Sets the owner_email of this WorkflowDef.


        :param owner_email: The owner_email of this WorkflowDef.  # noqa: E501
        :type: str
        """

        self._owner_email = owner_email

    @property
    def timeout_policy(self):
        """Gets the timeout_policy of this WorkflowDef.  # noqa: E501


        :return: The timeout_policy of this WorkflowDef.  # noqa: E501
        :rtype: str
        """
        return self._timeout_policy

    @timeout_policy.setter
    def timeout_policy(self, timeout_policy):
        """Sets the timeout_policy of this WorkflowDef.


        :param timeout_policy: The timeout_policy of this WorkflowDef.  # noqa: E501
        :type: str
        """
        allowed_values = ["TIME_OUT_WF", "ALERT_ONLY"]  # noqa: E501
        if timeout_policy not in allowed_values:
            raise ValueError(
                "Invalid value for `timeout_policy` ({0}), must be one of {1}".format(  # noqa: E501
                    timeout_policy, allowed_values
                )
            )

        self._timeout_policy = timeout_policy

    @property
    def timeout_seconds(self):
        """Gets the timeout_seconds of this WorkflowDef.  # noqa: E501


        :return: The timeout_seconds of this WorkflowDef.  # noqa: E501
        :rtype: int
        """
        return self._timeout_seconds

    @timeout_seconds.setter
    def timeout_seconds(self, timeout_seconds):
        """Sets the timeout_seconds of this WorkflowDef.


        :param timeout_seconds: The timeout_seconds of this WorkflowDef.  # noqa: E501
        :type: int
        """
        self._timeout_seconds = timeout_seconds

    @property
    def variables(self):
        """Gets the variables of this WorkflowDef.  # noqa: E501


        :return: The variables of this WorkflowDef.  # noqa: E501
        :rtype: dict(str, object)
        """
        return self._variables

    @variables.setter
    def variables(self, variables):
        """Sets the variables of this WorkflowDef.


        :param variables: The variables of this WorkflowDef.  # noqa: E501
        :type: dict(str, object)
        """

        self._variables = variables

    @property
    def input_template(self):
        """Gets the input_template of this WorkflowDef.  # noqa: E501


        :return: The input_template of this WorkflowDef.  # noqa: E501
        :rtype: dict(str, object)
        """
        return self._input_template

    @input_template.setter
    def input_template(self, input_template):
        """Sets the input_template of this WorkflowDef.


        :param input_template: The input_template of this WorkflowDef.  # noqa: E501
        :type: dict(str, object)
        """

        self._input_template = input_template

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
        if issubclass(WorkflowDef, dict):
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
        if not isinstance(other, WorkflowDef):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other

    def toJSON(self):
        return object_mapper.to_json(obj=self)


def to_workflow_def(data: str = None, json_data: dict = None) -> WorkflowDef:
    if json_data is not None:
        return object_mapper.from_json(json_data, WorkflowDef)
    if data is not None:
        return object_mapper.from_json(json.loads(data), WorkflowDef)
    raise Exception("missing data or json_data parameter")
