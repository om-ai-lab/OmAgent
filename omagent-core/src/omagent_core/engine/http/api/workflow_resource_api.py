from __future__ import absolute_import

import re  # noqa: F401
import uuid

# python 2 and python 3 compatibility library
import six
from omagent_core.engine.http.api_client import ApiClient


class WorkflowResourceApi(object):
    def __init__(self, api_client=None):
        if api_client is None:
            api_client = ApiClient()
        self.api_client = api_client

    def decide(self, workflow_id, **kwargs):  # noqa: E501
        """Starts the decision task for a workflow  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.decide(workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str workflow_id: (required)
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.decide_with_http_info(workflow_id, **kwargs)  # noqa: E501
        else:
            (data) = self.decide_with_http_info(workflow_id, **kwargs)  # noqa: E501
            return data

    def decide_with_http_info(self, workflow_id, **kwargs):  # noqa: E501
        """Starts the decision task for a workflow  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.decide_with_http_info(workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str workflow_id: (required)
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ["workflow_id"]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'" " to method decide" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'workflow_id' is set
        if "workflow_id" not in params or params["workflow_id"] is None:
            raise ValueError(
                "Missing the required parameter `workflow_id` when calling `decide`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "workflow_id" in params:
            path_params["workflowId"] = params["workflow_id"]  # noqa: E501

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # Authentication setting
        auth_settings = ["api_key"]  # noqa: E501

        return self.api_client.call_api(
            "/workflow/decide/{workflowId}",
            "PUT",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type=None,  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def delete(self, workflow_id, **kwargs):  # noqa: E501
        """Removes the workflow from the system  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.delete(workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str workflow_id: (required)
        :param bool archive_workflow:
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.delete1_with_http_info(workflow_id, **kwargs)  # noqa: E501
        else:
            (data) = self.delete1_with_http_info(workflow_id, **kwargs)  # noqa: E501
            return data

    def delete1_with_http_info(self, workflow_id, **kwargs):  # noqa: E501
        """Removes the workflow from the system  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.delete1_with_http_info(workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str workflow_id: (required)
        :param bool archive_workflow:
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ["workflow_id", "archive_workflow"]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'" " to method delete1" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'workflow_id' is set
        if "workflow_id" not in params or params["workflow_id"] is None:
            raise ValueError(
                "Missing the required parameter `workflow_id` when calling `delete1`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "workflow_id" in params:
            path_params["workflowId"] = params["workflow_id"]  # noqa: E501

        query_params = []
        if "archive_workflow" in params:
            query_params.append(
                ("archiveWorkflow", params["archive_workflow"])
            )  # noqa: E501

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # Authentication setting
        auth_settings = ["api_key"]  # noqa: E501

        return self.api_client.call_api(
            "/workflow/{workflowId}/remove",
            "DELETE",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type=None,  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def execute_workflow(self, body, request_id, name, version, **kwargs):  # noqa: E501
        if request_id is None:
            request_id = str(uuid.uuid4())
        """Execute a workflow synchronously  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.execute_workflow(body, request_id, name, version, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param StartWorkflowRequest body: (required)
        :param str request_id: (required)
        :param str name: (required)
        :param int version: (required)
        :param str wait_until_task_ref:
        :param int wait_for_seconds:
        :return: WorkflowRun
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.execute_workflow_with_http_info(
                body, request_id, name, version, **kwargs
            )  # noqa: E501
        else:
            (data) = self.execute_workflow_with_http_info(
                body, request_id, name, version, **kwargs
            )  # noqa: E501
            return data

    def execute_workflow_with_http_info(
        self, body, request_id, name, version, **kwargs
    ):  # noqa: E501
        """Execute a workflow synchronously  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.execute_workflow_with_http_info(body, request_id, name, version, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param StartWorkflowRequest body: (required)
        :param str request_id: (required)
        :param str name: (required)
        :param int version: (required)
        :param str wait_until_task_ref:
        :param int wait_for_seconds:
        :return: WorkflowRun
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = [
            "body",
            "request_id",
            "name",
            "version",
            "wait_until_task_ref",
            "wait_for_seconds",
        ]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method execute_workflow" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'body' is set
        if "body" not in params or params["body"] is None:
            raise ValueError(
                "Missing the required parameter `body` when calling `execute_workflow`"
            )  # noqa: E501
        # verify the required parameter 'request_id' is set
        if "request_id" not in params or params["request_id"] is None:
            raise ValueError(
                "Missing the required parameter `request_id` when calling `execute_workflow`"
            )  # noqa: E501
        # verify the required parameter 'name' is set
        if "name" not in params or params["name"] is None:
            raise ValueError(
                "Missing the required parameter `name` when calling `execute_workflow`"
            )  # noqa: E501
        # verify the required parameter 'version' is set
        if "version" not in params or params["version"] is None:
            raise ValueError(
                "Missing the required parameter `version` when calling `execute_workflow`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "name" in params:
            path_params["name"] = params["name"]  # noqa: E501
        if "version" in params:
            path_params["version"] = params["version"]  # noqa: E501

        query_params = []
        if "request_id" in params:
            query_params.append(("requestId", params["request_id"]))  # noqa: E501
        if "wait_until_task_ref" in params:
            query_params.append(
                ("waitUntilTaskRef", params["wait_until_task_ref"])
            )  # noqa: E501
        if "wait_for_seconds" in params:
            query_params.append(
                ("waitForSeconds", params["wait_for_seconds"])
            )  # noqa: E501

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        if "body" in params:
            body_params = params["body"]
        # HTTP header `Accept`
        header_params["Accept"] = self.api_client.select_header_accept(
            ["application/json"]
        )  # noqa: E501

        # HTTP header `Content-Type`
        header_params["Content-Type"] = (
            self.api_client.select_header_content_type(  # noqa: E501
                ["application/json"]
            )
        )  # noqa: E501

        # Authentication setting
        auth_settings = ["api_key"]  # noqa: E501

        return self.api_client.call_api(
            "/workflow/execute/{name}/{version}",
            "POST",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type="WorkflowRun",  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def execute_workflow_as_api(self, body, name, **kwargs):  # noqa: E501
        """Execute a workflow synchronously with input and outputs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.execute_workflow_as_api(body, name, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param dict(str, object) body: (required)
        :param str name: (required)
        :param str request_id:
        :param str wait_until_task_ref:
        :param int wait_for_seconds:
        :param str authorization:
        :param int version:
        :return: dict(str, object)
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.execute_workflow_as_api_with_http_info(
                body, name, **kwargs
            )  # noqa: E501
        else:
            (data) = self.execute_workflow_as_api_with_http_info(
                body, name, **kwargs
            )  # noqa: E501
            return data

    def execute_workflow_as_api_with_http_info(
        self, body, name, **kwargs
    ):  # noqa: E501
        """Execute a workflow synchronously with input and outputs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.execute_workflow_as_api_with_http_info(body, name, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param dict(str, object) body: (required)
        :param str name: (required)
        :param str request_id:
        :param str wait_until_task_ref:
        :param int wait_for_seconds:
        :param str authorization:
        :param int version:
        :return: dict(str, object)
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = [
            "body",
            "name",
            "request_id",
            "wait_until_task_ref",
            "wait_for_seconds",
            "authorization",
            "version",
        ]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method execute_workflow_as_api" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'body' is set
        if "body" not in params or params["body"] is None:
            raise ValueError(
                "Missing the required parameter `body` when calling `execute_workflow_as_api`"
            )  # noqa: E501
        # verify the required parameter 'name' is set
        if "name" not in params or params["name"] is None:
            raise ValueError(
                "Missing the required parameter `name` when calling `execute_workflow_as_api`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "name" in params:
            path_params["name"] = params["name"]  # noqa: E501

        query_params = []
        if "version" in params:
            query_params.append(("version", params["version"]))  # noqa: E501

        header_params = {}
        if "request_id" in params:
            header_params["requestId"] = params["request_id"]  # noqa: E501
        if "wait_until_task_ref" in params:
            header_params["waitUntilTaskRef"] = params[
                "wait_until_task_ref"
            ]  # noqa: E501
        if "wait_for_seconds" in params:
            header_params["waitForSeconds"] = params["wait_for_seconds"]  # noqa: E501
        if "authorization" in params:
            header_params["authorization"] = params["authorization"]  # noqa: E501

        form_params = []
        local_var_files = {}

        body_params = None
        if "body" in params:
            body_params = params["body"]
        # HTTP header `Accept`
        header_params["Accept"] = self.api_client.select_header_accept(
            ["application/json"]
        )  # noqa: E501

        # HTTP header `Content-Type`
        header_params["Content-Type"] = (
            self.api_client.select_header_content_type(  # noqa: E501
                ["application/json"]
            )
        )  # noqa: E501

        # Authentication setting
        auth_settings = ["api_key"]  # noqa: E501

        return self.api_client.call_api(
            "/workflow/execute/{name}",
            "POST",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type="dict(str, object)",  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def execute_workflow_as_get_api(self, name, **kwargs):  # noqa: E501
        """Execute a workflow synchronously with input and outputs using get api  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.execute_workflow_as_get_api(name, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str name: (required)
        :param int version:
        :param str request_id:
        :param str wait_until_task_ref:
        :param int wait_for_seconds:
        :param str authorization:
        :return: dict(str, object)
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.execute_workflow_as_get_api_with_http_info(
                name, **kwargs
            )  # noqa: E501
        else:
            (data) = self.execute_workflow_as_get_api_with_http_info(
                name, **kwargs
            )  # noqa: E501
            return data

    def execute_workflow_as_get_api_with_http_info(self, name, **kwargs):  # noqa: E501
        """Execute a workflow synchronously with input and outputs using get api  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.execute_workflow_as_get_api_with_http_info(name, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str name: (required)
        :param int version:
        :param str request_id:
        :param str wait_until_task_ref:
        :param int wait_for_seconds:
        :param str authorization:
        :return: dict(str, object)
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = [
            "name",
            "version",
            "request_id",
            "wait_until_task_ref",
            "wait_for_seconds",
            "authorization",
        ]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method execute_workflow_as_get_api" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'name' is set
        if "name" not in params or params["name"] is None:
            raise ValueError(
                "Missing the required parameter `name` when calling `execute_workflow_as_get_api`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "name" in params:
            path_params["name"] = params["name"]  # noqa: E501

        query_params = []
        if "version" in params:
            query_params.append(("version", params["version"]))  # noqa: E501

        header_params = {}
        if "request_id" in params:
            header_params["requestId"] = params["request_id"]  # noqa: E501
        if "wait_until_task_ref" in params:
            header_params["waitUntilTaskRef"] = params[
                "wait_until_task_ref"
            ]  # noqa: E501
        if "wait_for_seconds" in params:
            header_params["waitForSeconds"] = params["wait_for_seconds"]  # noqa: E501
        if "authorization" in params:
            header_params["authorization"] = params["authorization"]  # noqa: E501

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params["Accept"] = self.api_client.select_header_accept(
            ["application/json"]
        )  # noqa: E501

        # Authentication setting
        auth_settings = ["api_key"]  # noqa: E501

        return self.api_client.call_api(
            "/workflow/execute/{name}",
            "GET",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type="dict(str, object)",  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def get_execution_status(self, workflow_id, **kwargs):  # noqa: E501
        """Gets the workflow by workflow id  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_execution_status(workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str workflow_id: (required)
        :param bool include_tasks:
        :param bool summarize:
        :return: Workflow
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.get_execution_status_with_http_info(
                workflow_id, **kwargs
            )  # noqa: E501
        else:
            (data) = self.get_execution_status_with_http_info(
                workflow_id, **kwargs
            )  # noqa: E501
            return data

    def get_execution_status_with_http_info(self, workflow_id, **kwargs):  # noqa: E501
        """Gets the workflow by workflow id  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_execution_status_with_http_info(workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str workflow_id: (required)
        :param bool include_tasks:
        :param bool summarize:
        :return: Workflow
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ["workflow_id", "include_tasks", "summarize"]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method get_execution_status" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'workflow_id' is set
        if "workflow_id" not in params or params["workflow_id"] is None:
            raise ValueError(
                "Missing the required parameter `workflow_id` when calling `get_execution_status`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "workflow_id" in params:
            path_params["workflowId"] = params["workflow_id"]  # noqa: E501

        query_params = []
        if "include_tasks" in params:
            query_params.append(("includeTasks", params["include_tasks"]))  # noqa: E501
        if "summarize" in params:
            query_params.append(("summarize", params["summarize"]))  # noqa: E501

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params["Accept"] = self.api_client.select_header_accept(
            ["*/*"]
        )  # noqa: E501

        # Authentication setting
        auth_settings = ["api_key"]  # noqa: E501

        return self.api_client.call_api(
            "/workflow/{workflowId}",
            "GET",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type="Workflow",  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def get_execution_status_task_list(self, workflow_id, **kwargs):  # noqa: E501
        """Gets the workflow tasks by workflow id  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_execution_status_task_list(workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str workflow_id: (required)
        :param int start:
        :param int count:
        :param list[str] status:
        :return: TaskListSearchResultSummary
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.get_execution_status_task_list_with_http_info(
                workflow_id, **kwargs
            )  # noqa: E501
        else:
            (data) = self.get_execution_status_task_list_with_http_info(
                workflow_id, **kwargs
            )  # noqa: E501
            return data

    def get_execution_status_task_list_with_http_info(
        self, workflow_id, **kwargs
    ):  # noqa: E501
        """Gets the workflow tasks by workflow id  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_execution_status_task_list_with_http_info(workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str workflow_id: (required)
        :param int start:
        :param int count:
        :param list[str] status:
        :return: TaskListSearchResultSummary
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ["workflow_id", "start", "count", "status"]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method get_execution_status_task_list" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'workflow_id' is set
        if "workflow_id" not in params or params["workflow_id"] is None:
            raise ValueError(
                "Missing the required parameter `workflow_id` when calling `get_execution_status_task_list`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "workflow_id" in params:
            path_params["workflowId"] = params["workflow_id"]  # noqa: E501

        query_params = []
        if "start" in params:
            query_params.append(("start", params["start"]))  # noqa: E501
        if "count" in params:
            query_params.append(("count", params["count"]))  # noqa: E501
        if "status" in params:
            query_params.append(("status", params["status"]))  # noqa: E501
            collection_formats["status"] = "multi"  # noqa: E501

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params["Accept"] = self.api_client.select_header_accept(
            ["*/*"]
        )  # noqa: E501

        # Authentication setting
        auth_settings = ["api_key"]  # noqa: E501

        return self.api_client.call_api(
            "/workflow/{workflowId}/tasks",
            "GET",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type="TaskListSearchResultSummary",  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def get_running_workflow(self, name, **kwargs):  # noqa: E501
        """Retrieve all the running workflows  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_running_workflow(name, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str name: (required)
        :param int version:
        :param int start_time:
        :param int end_time:
        :return: list[str]
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.get_running_workflow_with_http_info(
                name, **kwargs
            )  # noqa: E501
        else:
            (data) = self.get_running_workflow_with_http_info(
                name, **kwargs
            )  # noqa: E501
            return data

    def get_running_workflow_with_http_info(self, name, **kwargs):  # noqa: E501
        """Retrieve all the running workflows  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_running_workflow_with_http_info(name, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str name: (required)
        :param int version:
        :param int start_time:
        :param int end_time:
        :return: list[str]
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ["name", "version", "start_time", "end_time"]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method get_running_workflow" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'name' is set
        if "name" not in params or params["name"] is None:
            raise ValueError(
                "Missing the required parameter `name` when calling `get_running_workflow`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "name" in params:
            path_params["name"] = params["name"]  # noqa: E501

        query_params = []
        if "version" in params:
            query_params.append(("version", params["version"]))  # noqa: E501
        if "start_time" in params:
            query_params.append(("startTime", params["start_time"]))  # noqa: E501
        if "end_time" in params:
            query_params.append(("endTime", params["end_time"]))  # noqa: E501

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params["Accept"] = self.api_client.select_header_accept(
            ["*/*"]
        )  # noqa: E501

        # Authentication setting
        auth_settings = ["api_key"]  # noqa: E501

        return self.api_client.call_api(
            "/workflow/running/{name}",
            "GET",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type="list[str]",  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def get_workflow_status_summary(self, workflow_id, **kwargs):  # noqa: E501
        """Gets the workflow by workflow id  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_workflow_status_summary(workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str workflow_id: (required)
        :param bool include_output:
        :param bool include_variables:
        :return: WorkflowStatus
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.get_workflow_status_summary_with_http_info(
                workflow_id, **kwargs
            )  # noqa: E501
        else:
            (data) = self.get_workflow_status_summary_with_http_info(
                workflow_id, **kwargs
            )  # noqa: E501
            return data

    def get_workflow_status_summary_with_http_info(
        self, workflow_id, **kwargs
    ):  # noqa: E501
        """Gets the workflow by workflow id  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_workflow_status_summary_with_http_info(workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str workflow_id: (required)
        :param bool include_output:
        :param bool include_variables:
        :return: WorkflowStatus
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = [
            "workflow_id",
            "include_output",
            "include_variables",
        ]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method get_workflow_status_summary" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'workflow_id' is set
        if "workflow_id" not in params or params["workflow_id"] is None:
            raise ValueError(
                "Missing the required parameter `workflow_id` when calling `get_workflow_status_summary`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "workflow_id" in params:
            path_params["workflowId"] = params["workflow_id"]  # noqa: E501

        query_params = []
        if "include_output" in params:
            query_params.append(
                ("includeOutput", params["include_output"])
            )  # noqa: E501
        if "include_variables" in params:
            query_params.append(
                ("includeVariables", params["include_variables"])
            )  # noqa: E501

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params["Accept"] = self.api_client.select_header_accept(
            ["*/*"]
        )  # noqa: E501

        # Authentication setting
        auth_settings = ["api_key"]  # noqa: E501

        return self.api_client.call_api(
            "/workflow/{workflowId}",
            "GET",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type="WorkflowStatus",  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def get_workflows(self, body, name, **kwargs):  # noqa: E501
        """Lists workflows for the given correlation id list  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_workflows(body, name, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param list[str] body: (required)
        :param str name: (required)
        :param bool include_closed:
        :param bool include_tasks:
        :return: dict(str, list[Workflow])
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.get_workflows_with_http_info(body, name, **kwargs)  # noqa: E501
        else:
            (data) = self.get_workflows_with_http_info(
                body, name, **kwargs
            )  # noqa: E501
            return data

    def get_workflows_with_http_info(self, body, name, **kwargs):  # noqa: E501
        """Lists workflows for the given correlation id list  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_workflows_with_http_info(body, name, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param list[str] body: (required)
        :param str name: (required)
        :param bool include_closed:
        :param bool include_tasks:
        :return: dict(str, list[Workflow])
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ["body", "name", "include_closed", "include_tasks"]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method get_workflows" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'body' is set
        if "body" not in params or params["body"] is None:
            raise ValueError(
                "Missing the required parameter `body` when calling `get_workflows`"
            )  # noqa: E501
        # verify the required parameter 'name' is set
        if "name" not in params or params["name"] is None:
            raise ValueError(
                "Missing the required parameter `name` when calling `get_workflows`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "name" in params:
            path_params["name"] = params["name"]  # noqa: E501

        query_params = []
        if "include_closed" in params:
            query_params.append(
                ("includeClosed", params["include_closed"])
            )  # noqa: E501
        if "include_tasks" in params:
            query_params.append(("includeTasks", params["include_tasks"]))  # noqa: E501

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        if "body" in params:
            body_params = params["body"]
        # HTTP header `Accept`
        header_params["Accept"] = self.api_client.select_header_accept(
            ["*/*"]
        )  # noqa: E501

        # HTTP header `Content-Type`
        header_params["Content-Type"] = (
            self.api_client.select_header_content_type(  # noqa: E501
                ["application/json"]
            )
        )  # noqa: E501

        # Authentication setting
        auth_settings = ["api_key"]  # noqa: E501

        return self.api_client.call_api(
            "/workflow/{name}/correlated",
            "POST",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type="dict(str, list[Workflow])",  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def get_workflows_by_correlation_id_in_batch(self, body, **kwargs):  # noqa: E501
        """Lists workflows for the given correlation id list and workflow name list  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_workflows_by_correlation_id_in_batch(body, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param CorrelationIdsSearchRequest body: (required)
        :param bool include_closed:
        :param bool include_tasks:
        :return: dict(str, list[Workflow])
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.get_workflows1_with_http_info(body, **kwargs)  # noqa: E501
        else:
            (data) = self.get_workflows1_with_http_info(body, **kwargs)  # noqa: E501
            return data

    def get_workflows_batch(self, body, **kwargs):  # noqa: E501
        """
        deprecated:: Please use get_workflows_by_correlation_id_in_batch
        Lists workflows for the given correlation id list and workflow name list  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_workflows_by_correlation_id_in_batch(body, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param CorrelationIdsSearchRequest body: (required)
        :param bool include_closed:
        :param bool include_tasks:
        :return: dict(str, list[Workflow])
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.get_workflows1_with_http_info(body, **kwargs)  # noqa: E501
        else:
            (data) = self.get_workflows1_with_http_info(body, **kwargs)  # noqa: E501
            return data

    def get_workflows1_with_http_info(self, body, **kwargs):  # noqa: E501
        """Lists workflows for the given correlation id list and workflow name list  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_workflows1_with_http_info(body, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param CorrelationIdsSearchRequest body: (required)
        :param bool include_closed:
        :param bool include_tasks:
        :return: dict(str, list[Workflow])
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ["body", "include_closed", "include_tasks"]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method get_workflows1" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'body' is set
        if "body" not in params or params["body"] is None:
            raise ValueError(
                "Missing the required parameter `body` when calling `get_workflows1`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}

        query_params = []
        if "include_closed" in params:
            query_params.append(
                ("includeClosed", params["include_closed"])
            )  # noqa: E501
        if "include_tasks" in params:
            query_params.append(("includeTasks", params["include_tasks"]))  # noqa: E501

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        if "body" in params:
            body_params = params["body"]
        # HTTP header `Accept`
        header_params["Accept"] = self.api_client.select_header_accept(
            ["*/*"]
        )  # noqa: E501

        # HTTP header `Content-Type`
        header_params["Content-Type"] = (
            self.api_client.select_header_content_type(  # noqa: E501
                ["application/json"]
            )
        )  # noqa: E501

        # Authentication setting
        auth_settings = ["api_key"]  # noqa: E501

        return self.api_client.call_api(
            "/workflow/correlated/batch",
            "POST",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type="dict(str, list[Workflow])",  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def get_workflows2(self, name, correlation_id, **kwargs):  # noqa: E501
        """Lists workflows for the given correlation id  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_workflows2(name, correlation_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str name: (required)
        :param str correlation_id: (required)
        :param bool include_closed:
        :param bool include_tasks:
        :return: list[Workflow]
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.get_workflows2_with_http_info(
                name, correlation_id, **kwargs
            )  # noqa: E501
        else:
            (data) = self.get_workflows2_with_http_info(
                name, correlation_id, **kwargs
            )  # noqa: E501
            return data

    def get_workflows2_with_http_info(
        self, name, correlation_id, **kwargs
    ):  # noqa: E501
        """Lists workflows for the given correlation id  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_workflows2_with_http_info(name, correlation_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str name: (required)
        :param str correlation_id: (required)
        :param bool include_closed:
        :param bool include_tasks:
        :return: list[Workflow]
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = [
            "name",
            "correlation_id",
            "include_closed",
            "include_tasks",
        ]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method get_workflows2" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'name' is set
        if "name" not in params or params["name"] is None:
            raise ValueError(
                "Missing the required parameter `name` when calling `get_workflows2`"
            )  # noqa: E501
        # verify the required parameter 'correlation_id' is set
        if "correlation_id" not in params or params["correlation_id"] is None:
            raise ValueError(
                "Missing the required parameter `correlation_id` when calling `get_workflows2`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "name" in params:
            path_params["name"] = params["name"]  # noqa: E501
        if "correlation_id" in params:
            path_params["correlationId"] = params["correlation_id"]  # noqa: E501

        query_params = []
        if "include_closed" in params:
            query_params.append(
                ("includeClosed", params["include_closed"])
            )  # noqa: E501
        if "include_tasks" in params:
            query_params.append(("includeTasks", params["include_tasks"]))  # noqa: E501

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params["Accept"] = self.api_client.select_header_accept(
            ["*/*"]
        )  # noqa: E501

        # Authentication setting
        auth_settings = ["api_key"]  # noqa: E501

        return self.api_client.call_api(
            "/workflow/{name}/correlated/{correlationId}",
            "GET",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type="list[Workflow]",  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def jump_to_task(self, body, workflow_id, **kwargs):  # noqa: E501
        """Jump workflow execution to given task  # noqa: E501

        Jump workflow execution to given task.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.jump_to_task(body, workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param dict(str, object) body: (required)
        :param str workflow_id: (required)
        :param str task_reference_name:
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.jump_to_task_with_http_info(
                body, workflow_id, **kwargs
            )  # noqa: E501
        else:
            (data) = self.jump_to_task_with_http_info(
                body, workflow_id, **kwargs
            )  # noqa: E501
            return data

    def jump_to_task_with_http_info(self, body, workflow_id, **kwargs):  # noqa: E501
        """Jump workflow execution to given task  # noqa: E501

        Jump workflow execution to given task.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.jump_to_task_with_http_info(body, workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param dict(str, object) body: (required)
        :param str workflow_id: (required)
        :param str task_reference_name:
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ["body", "workflow_id", "task_reference_name"]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method jump_to_task" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'body' is set
        if "body" not in params or params["body"] is None:
            raise ValueError(
                "Missing the required parameter `body` when calling `jump_to_task`"
            )  # noqa: E501
        # verify the required parameter 'workflow_id' is set
        if "workflow_id" not in params or params["workflow_id"] is None:
            raise ValueError(
                "Missing the required parameter `workflow_id` when calling `jump_to_task`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "workflow_id" in params:
            path_params["workflowId"] = params["workflow_id"]  # noqa: E501

        query_params = []
        if "task_reference_name" in params:
            query_params.append(
                ("taskReferenceName", params["task_reference_name"])
            )  # noqa: E501

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        if "body" in params:
            body_params = params["body"]
        # HTTP header `Content-Type`
        header_params["Content-Type"] = (
            self.api_client.select_header_content_type(  # noqa: E501
                ["application/json"]
            )
        )  # noqa: E501

        # Authentication setting
        auth_settings = ["api_key"]  # noqa: E501

        return self.api_client.call_api(
            "/workflow/{workflowId}/jump/{taskReferenceName}",
            "POST",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type=None,  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def pause_workflow1(self, workflow_id, **kwargs):  # noqa: E501
        """
        deprecated:: Please use pause_workflow(workflow_id) method
        Parameters
        ----------
        workflow_id
        kwargs

        Returns
        -------

        """
        self.pause_workflow(workflow_id)

    def pause_workflow(self, workflow_id, **kwargs):  # noqa: E501
        """Pauses the workflow  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.pause_workflow(workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str workflow_id: (required)
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.pause_workflow_with_http_info(
                workflow_id, **kwargs
            )  # noqa: E501
        else:
            (data) = self.pause_workflow_with_http_info(
                workflow_id, **kwargs
            )  # noqa: E501
            return data

    def pause_workflow_with_http_info(self, workflow_id, **kwargs):  # noqa: E501
        """Pauses the workflow  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.pause_workflow_with_http_info(workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str workflow_id: (required)
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ["workflow_id"]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method pause_workflow" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'workflow_id' is set
        if "workflow_id" not in params or params["workflow_id"] is None:
            raise ValueError(
                "Missing the required parameter `workflow_id` when calling `pause_workflow`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "workflow_id" in params:
            path_params["workflowId"] = params["workflow_id"]  # noqa: E501

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # Authentication setting
        auth_settings = ["api_key"]  # noqa: E501

        return self.api_client.call_api(
            "/workflow/{workflowId}/pause",
            "PUT",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type=None,  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def rerun(self, body, workflow_id, **kwargs):  # noqa: E501
        """Reruns the workflow from a specific task  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.rerun(body, workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param RerunWorkflowRequest body: (required)
        :param str workflow_id: (required)
        :return: str
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.rerun_with_http_info(body, workflow_id, **kwargs)  # noqa: E501
        else:
            (data) = self.rerun_with_http_info(
                body, workflow_id, **kwargs
            )  # noqa: E501
            return data

    def rerun_with_http_info(self, body, workflow_id, **kwargs):  # noqa: E501
        """Reruns the workflow from a specific task  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.rerun_with_http_info(body, workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param RerunWorkflowRequest body: (required)
        :param str workflow_id: (required)
        :return: str
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ["body", "workflow_id"]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'" " to method rerun" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'body' is set
        if "body" not in params or params["body"] is None:
            raise ValueError(
                "Missing the required parameter `body` when calling `rerun`"
            )  # noqa: E501
        # verify the required parameter 'workflow_id' is set
        if "workflow_id" not in params or params["workflow_id"] is None:
            raise ValueError(
                "Missing the required parameter `workflow_id` when calling `rerun`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "workflow_id" in params:
            path_params["workflowId"] = params["workflow_id"]  # noqa: E501

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        if "body" in params:
            body_params = params["body"]
        # HTTP header `Accept`
        header_params["Accept"] = self.api_client.select_header_accept(
            ["text/plain"]
        )  # noqa: E501

        # HTTP header `Content-Type`
        header_params["Content-Type"] = (
            self.api_client.select_header_content_type(  # noqa: E501
                ["application/json"]
            )
        )  # noqa: E501

        # Authentication setting
        auth_settings = ["api_key"]  # noqa: E501

        return self.api_client.call_api(
            "/workflow/{workflowId}/rerun",
            "POST",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type="str",  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def reset_workflow(self, workflow_id, **kwargs):  # noqa: E501
        """Resets callback times of all non-terminal SIMPLE tasks to 0  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.reset_workflow(workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str workflow_id: (required)
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.reset_workflow_with_http_info(
                workflow_id, **kwargs
            )  # noqa: E501
        else:
            (data) = self.reset_workflow_with_http_info(
                workflow_id, **kwargs
            )  # noqa: E501
            return data

    def reset_workflow_with_http_info(self, workflow_id, **kwargs):  # noqa: E501
        """Resets callback times of all non-terminal SIMPLE tasks to 0  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.reset_workflow_with_http_info(workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str workflow_id: (required)
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ["workflow_id"]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method reset_workflow" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'workflow_id' is set
        if "workflow_id" not in params or params["workflow_id"] is None:
            raise ValueError(
                "Missing the required parameter `workflow_id` when calling `reset_workflow`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "workflow_id" in params:
            path_params["workflowId"] = params["workflow_id"]  # noqa: E501

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # Authentication setting
        auth_settings = ["api_key"]  # noqa: E501

        return self.api_client.call_api(
            "/workflow/{workflowId}/resetcallbacks",
            "POST",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type=None,  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def restart1(self, workflow_id, **kwargs):  # noqa: E501
        """
        deprecated:: Please use restart(workflow_id) method
        Parameters
        ----------
        workflow_id
        kwargs

        Returns
        -------

        """
        return self.restart(workflow_id)

    def restart(self, workflow_id, **kwargs):  # noqa: E501
        """Restarts a completed workflow  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.restart(workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str workflow_id: (required)
        :param bool use_latest_definitions:
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.restart_with_http_info(workflow_id, **kwargs)  # noqa: E501
        else:
            (data) = self.restart_with_http_info(workflow_id, **kwargs)  # noqa: E501
            return data

    def restart_with_http_info(self, workflow_id, **kwargs):  # noqa: E501
        """Restarts a completed workflow  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.restart_with_http_info(workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str workflow_id: (required)
        :param bool use_latest_definitions:
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ["workflow_id", "use_latest_definitions"]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'" " to method restart" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'workflow_id' is set
        if "workflow_id" not in params or params["workflow_id"] is None:
            raise ValueError(
                "Missing the required parameter `workflow_id` when calling `restart`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "workflow_id" in params:
            path_params["workflowId"] = params["workflow_id"]  # noqa: E501

        query_params = []
        if "use_latest_definitions" in params:
            query_params.append(
                ("useLatestDefinitions", params["use_latest_definitions"])
            )  # noqa: E501

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # Authentication setting
        auth_settings = ["api_key"]  # noqa: E501

        return self.api_client.call_api(
            "/workflow/{workflowId}/restart",
            "POST",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type=None,  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def resume_workflow1(self, workflow_id):  # noqa: E501
        """
        deprecated:: Please use resume_workflow(workflow_id) method
        Parameters
        ----------
        workflow_id

        Returns
        -------

        """
        return self.resume_workflow(workflow_id)

    def resume_workflow(self, workflow_id, **kwargs):  # noqa: E501
        """Resumes the workflow  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.resume_workflow(workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str workflow_id: (required)
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.resume_workflow_with_http_info(
                workflow_id, **kwargs
            )  # noqa: E501
        else:
            (data) = self.resume_workflow_with_http_info(
                workflow_id, **kwargs
            )  # noqa: E501
            return data

    def resume_workflow_with_http_info(self, workflow_id, **kwargs):  # noqa: E501
        """Resumes the workflow  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.resume_workflow_with_http_info(workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str workflow_id: (required)
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ["workflow_id"]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method resume_workflow" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'workflow_id' is set
        if "workflow_id" not in params or params["workflow_id"] is None:
            raise ValueError(
                "Missing the required parameter `workflow_id` when calling `resume_workflow`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "workflow_id" in params:
            path_params["workflowId"] = params["workflow_id"]  # noqa: E501

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # Authentication setting
        auth_settings = ["api_key"]  # noqa: E501

        return self.api_client.call_api(
            "/workflow/{workflowId}/resume",
            "PUT",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type=None,  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def retry1(self, workflow_id, **kwargs):  # noqa: E501
        """
        deprecated:: Please use retry(workflow_id) method
        Parameters
        ----------
        workflow_id
        kwargs

        Returns
        -------

        """
        return self.retry(workflow_id)

    def retry(self, workflow_id, **kwargs):  # noqa: E501
        """Retries the last failed task  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.retry(workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str workflow_id: (required)
        :param bool resume_subworkflow_tasks:
        :param bool retry_if_retried_by_parent:
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.retry_with_http_info(workflow_id, **kwargs)  # noqa: E501
        else:
            (data) = self.retry_with_http_info(workflow_id, **kwargs)  # noqa: E501
            return data

    def retry_with_http_info(self, workflow_id, **kwargs):  # noqa: E501
        """Retries the last failed task  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.retry_with_http_info(workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str workflow_id: (required)
        :param bool resume_subworkflow_tasks:
        :param bool retry_if_retried_by_parent:
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = [
            "workflow_id",
            "resume_subworkflow_tasks",
            "retry_if_retried_by_parent",
        ]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'" " to method retry" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'workflow_id' is set
        if "workflow_id" not in params or params["workflow_id"] is None:
            raise ValueError(
                "Missing the required parameter `workflow_id` when calling `retry`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "workflow_id" in params:
            path_params["workflowId"] = params["workflow_id"]  # noqa: E501

        query_params = []
        if "resume_subworkflow_tasks" in params:
            query_params.append(
                ("resumeSubworkflowTasks", params["resume_subworkflow_tasks"])
            )  # noqa: E501
        if "retry_if_retried_by_parent" in params:
            query_params.append(
                ("retryIfRetriedByParent", params["retry_if_retried_by_parent"])
            )  # noqa: E501

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # Authentication setting
        auth_settings = ["api_key"]  # noqa: E501

        return self.api_client.call_api(
            "/workflow/{workflowId}/retry",
            "POST",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type=None,  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def search(self, **kwargs):  # noqa: E501
        """Search for workflows based on payload and other parameters  # noqa: E501

        Search for workflows based on payload and other parameters. The query parameter accepts exact matches using `=` and `IN` on the following fields: `workflowId`, `correlationId`, `taskId`, `workflowType`, `taskType`, and `status`.  Matches using `=` can be written as `taskType = HTTP`.  Matches using `IN` are written as `status IN (SCHEDULED, IN_PROGRESS)`. The 'startTime' and 'modifiedTime' field uses unix timestamps and accepts queries using `<` and `>`, for example `startTime < 1696143600000`. Queries can be combined using `AND`, for example `taskType = HTTP AND status = SCHEDULED`.   # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.search(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str query_id:
        :param int start:
        :param int size:
        :param str free_text:
        :param str query:
        :param bool skip_cache:
        :return: ScrollableSearchResultWorkflowSummary
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.search_with_http_info(**kwargs)  # noqa: E501
        else:
            (data) = self.search_with_http_info(**kwargs)  # noqa: E501
            return data

    def search_with_http_info(self, **kwargs):  # noqa: E501
        """Search for workflows based on payload and other parameters  # noqa: E501

        Search for workflows based on payload and other parameters. The query parameter accepts exact matches using `=` and `IN` on the following fields: `workflowId`, `correlationId`, `taskId`, `workflowType`, `taskType`, and `status`.  Matches using `=` can be written as `taskType = HTTP`.  Matches using `IN` are written as `status IN (SCHEDULED, IN_PROGRESS)`. The 'startTime' and 'modifiedTime' field uses unix timestamps and accepts queries using `<` and `>`, for example `startTime < 1696143600000`. Queries can be combined using `AND`, for example `taskType = HTTP AND status = SCHEDULED`.   # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.search_with_http_info(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str query_id:
        :param int start:
        :param int size:
        :param str free_text:
        :param str query:
        :param bool skip_cache:
        :return: ScrollableSearchResultWorkflowSummary
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = [
            "query_id",
            "start",
            "size",
            "free_text",
            "query",
            "skip_cache",
        ]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'" " to method search" % key
                )
            params[key] = val
        del params["kwargs"]

        collection_formats = {}

        path_params = {}

        query_params = []
        if "query_id" in params:
            query_params.append(("queryId", params["query_id"]))  # noqa: E501
        if "start" in params:
            query_params.append(("start", params["start"]))  # noqa: E501
        if "size" in params:
            query_params.append(("size", params["size"]))  # noqa: E501
        if "free_text" in params:
            query_params.append(("freeText", params["free_text"]))  # noqa: E501
        if "query" in params:
            query_params.append(("query", params["query"]))  # noqa: E501
        if "skip_cache" in params:
            query_params.append(("skipCache", params["skip_cache"]))  # noqa: E501

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params["Accept"] = self.api_client.select_header_accept(
            ["*/*"]
        )  # noqa: E501

        # Authentication setting
        auth_settings = ["api_key"]  # noqa: E501

        return self.api_client.call_api(
            "/workflow/search",
            "GET",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type="ScrollableSearchResultWorkflowSummary",  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def skip_task_from_workflow(
        self, workflow_id, task_reference_name, skip_task_request, **kwargs
    ):  # noqa: E501
        """Skips a given task from a current running workflow  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.skip_task_from_workflow(workflow_id, task_reference_name, skip_task_request, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str workflow_id: (required)
        :param str task_reference_name: (required)
        :param SkipTaskRequest skip_task_request: (required)
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.skip_task_from_workflow_with_http_info(
                workflow_id, task_reference_name, skip_task_request, **kwargs
            )  # noqa: E501
        else:
            (data) = self.skip_task_from_workflow_with_http_info(
                workflow_id, task_reference_name, skip_task_request, **kwargs
            )  # noqa: E501
            return data

    def skip_task_from_workflow_with_http_info(
        self, workflow_id, task_reference_name, skip_task_request, **kwargs
    ):  # noqa: E501
        """Skips a given task from a current running workflow  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.skip_task_from_workflow_with_http_info(workflow_id, task_reference_name, skip_task_request, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str workflow_id: (required)
        :param str task_reference_name: (required)
        :param SkipTaskRequest skip_task_request: (required)
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = [
            "workflow_id",
            "task_reference_name",
            "skip_task_request",
        ]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method skip_task_from_workflow" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'workflow_id' is set
        if "workflow_id" not in params or params["workflow_id"] is None:
            raise ValueError(
                "Missing the required parameter `workflow_id` when calling `skip_task_from_workflow`"
            )  # noqa: E501
        # verify the required parameter 'task_reference_name' is set
        if "task_reference_name" not in params or params["task_reference_name"] is None:
            raise ValueError(
                "Missing the required parameter `task_reference_name` when calling `skip_task_from_workflow`"
            )  # noqa: E501
        # verify the required parameter 'skip_task_request' is set
        if "skip_task_request" not in params or params["skip_task_request"] is None:
            raise ValueError(
                "Missing the required parameter `skip_task_request` when calling `skip_task_from_workflow`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "workflow_id" in params:
            path_params["workflowId"] = params["workflow_id"]  # noqa: E501
        if "task_reference_name" in params:
            path_params["taskReferenceName"] = params[
                "task_reference_name"
            ]  # noqa: E501

        query_params = []
        if "skip_task_request" in params:
            query_params.append(
                ("skipTaskRequest", params["skip_task_request"])
            )  # noqa: E501

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # Authentication setting
        auth_settings = ["api_key"]  # noqa: E501

        return self.api_client.call_api(
            "/workflow/{workflowId}/skiptask/{taskReferenceName}",
            "PUT",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type=None,  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def start_workflow(self, body, **kwargs):  # noqa: E501
        """Start a new workflow with StartWorkflowRequest, which allows task to be executed in a domain  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.start_workflow(body, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param StartWorkflowRequest body: (required)
        :return: str
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.start_workflow_with_http_info(body, **kwargs)  # noqa: E501
        else:
            (data) = self.start_workflow_with_http_info(body, **kwargs)  # noqa: E501
            return data

    def start_workflow_with_http_info(self, body, **kwargs):  # noqa: E501
        """Start a new workflow with StartWorkflowRequest, which allows task to be executed in a domain  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.start_workflow_with_http_info(body, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param StartWorkflowRequest body: (required)
        :return: str
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ["body"]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method start_workflow" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'body' is set
        if "body" not in params or params["body"] is None:
            raise ValueError(
                "Missing the required parameter `body` when calling `start_workflow`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        if "body" in params:
            body_params = params["body"]
        # HTTP header `Accept`
        header_params["Accept"] = self.api_client.select_header_accept(
            ["text/plain"]
        )  # noqa: E501

        # HTTP header `Content-Type`
        header_params["Content-Type"] = (
            self.api_client.select_header_content_type(  # noqa: E501
                ["application/json"]
            )
        )  # noqa: E501

        # Authentication setting
        auth_settings = ["api_key"]  # noqa: E501

        return self.api_client.call_api(
            "/workflow",
            "POST",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type="str",  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def start_workflow1(self, body, name, **kwargs):  # noqa: E501
        """Start a new workflow. Returns the ID of the workflow instance that can be later used for tracking  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.start_workflow1(body, name, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param dict(str, object) body: (required)
        :param str name: (required)
        :param int version:
        :param str correlation_id:
        :param int priority:
        :return: str
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.start_workflow1_with_http_info(
                body, name, **kwargs
            )  # noqa: E501
        else:
            (data) = self.start_workflow1_with_http_info(
                body, name, **kwargs
            )  # noqa: E501
            return data

    def start_workflow1_with_http_info(self, body, name, **kwargs):  # noqa: E501
        """Start a new workflow. Returns the ID of the workflow instance that can be later used for tracking  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.start_workflow1_with_http_info(body, name, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param dict(str, object) body: (required)
        :param str name: (required)
        :param int version:
        :param str correlation_id:
        :param int priority:
        :return: str
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = [
            "body",
            "name",
            "version",
            "correlation_id",
            "priority",
        ]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method start_workflow1" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'body' is set
        if "body" not in params or params["body"] is None:
            raise ValueError(
                "Missing the required parameter `body` when calling `start_workflow1`"
            )  # noqa: E501
        # verify the required parameter 'name' is set
        if "name" not in params or params["name"] is None:
            raise ValueError(
                "Missing the required parameter `name` when calling `start_workflow1`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "name" in params:
            path_params["name"] = params["name"]  # noqa: E501

        query_params = []
        if "version" in params:
            query_params.append(("version", params["version"]))  # noqa: E501
        if "correlation_id" in params:
            query_params.append(
                ("correlationId", params["correlation_id"])
            )  # noqa: E501
        if "priority" in params:
            query_params.append(("priority", params["priority"]))  # noqa: E501

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        if "body" in params:
            body_params = params["body"]
        # HTTP header `Accept`
        header_params["Accept"] = self.api_client.select_header_accept(
            ["text/plain"]
        )  # noqa: E501

        # HTTP header `Content-Type`
        header_params["Content-Type"] = (
            self.api_client.select_header_content_type(  # noqa: E501
                ["application/json"]
            )
        )  # noqa: E501

        # Authentication setting
        auth_settings = ["api_key"]  # noqa: E501

        return self.api_client.call_api(
            "/workflow/{name}",
            "POST",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type="str",  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def terminate1(self, workflow_id, **kwargs):  # noqa: E501
        """
        deprecated:: Please use terminate(workflow_id) method
        Parameters
        ----------
        workflow_id
        kwargs

        Returns
        -------

        """
        options = {}
        if "triggerFailureWorkflow" in kwargs.keys():
            options["trigger_failure_workflow"] = kwargs["triggerFailureWorkflow"]

        return self.terminate(workflow_id, **options)

    def terminate(self, workflow_id, **kwargs):  # noqa: E501
        """Terminate workflow execution  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.terminate1(workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str workflow_id: (required)
        :param str reason:
        :param bool trigger_failure_workflow:
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if workflow_id is None:
            raise Exception("Missing workflow id")
        if kwargs.get("async_req"):
            return self.terminate1_with_http_info(workflow_id, **kwargs)  # noqa: E501
        else:
            (data) = self.terminate1_with_http_info(workflow_id, **kwargs)  # noqa: E501
            return data

    def terminate1_with_http_info(self, workflow_id, **kwargs):  # noqa: E501
        """Terminate workflow execution  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.terminate1_with_http_info(workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str workflow_id: (required)
        :param str reason:
        :param bool trigger_failure_workflow:
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ["workflow_id", "reason", "trigger_failure_workflow"]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method terminate1" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'workflow_id' is set
        if "workflow_id" not in params or params["workflow_id"] is None:
            raise ValueError(
                "Missing the required parameter `workflow_id` when calling `terminate1`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "workflow_id" in params:
            path_params["workflowId"] = params["workflow_id"]  # noqa: E501

        query_params = []
        if "reason" in params:
            query_params.append(("reason", params["reason"]))  # noqa: E501
        if "trigger_failure_workflow" in params:
            query_params.append(
                ("triggerFailureWorkflow", params["trigger_failure_workflow"])
            )  # noqa: E501

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # Authentication setting
        auth_settings = ["api_key"]  # noqa: E501

        return self.api_client.call_api(
            "/workflow/{workflowId}",
            "DELETE",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type=None,  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def test_workflow(self, body, **kwargs):  # noqa: E501
        """Test workflow execution using mock data  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.test_workflow(body, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param WorkflowTestRequest body: (required)
        :return: Workflow
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.test_workflow_with_http_info(body, **kwargs)  # noqa: E501
        else:
            (data) = self.test_workflow_with_http_info(body, **kwargs)  # noqa: E501
            return data

    def test_workflow_with_http_info(self, body, **kwargs):  # noqa: E501
        """Test workflow execution using mock data  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.test_workflow_with_http_info(body, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param WorkflowTestRequest body: (required)
        :return: Workflow
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ["body"]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method test_workflow" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'body' is set
        if "body" not in params or params["body"] is None:
            raise ValueError(
                "Missing the required parameter `body` when calling `test_workflow`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        if "body" in params:
            body_params = params["body"]
        # HTTP header `Accept`
        header_params["Accept"] = self.api_client.select_header_accept(
            ["application/json"]
        )  # noqa: E501

        # HTTP header `Content-Type`
        header_params["Content-Type"] = (
            self.api_client.select_header_content_type(  # noqa: E501
                ["application/json"]
            )
        )  # noqa: E501

        # Authentication setting
        auth_settings = ["api_key"]  # noqa: E501

        return self.api_client.call_api(
            "/workflow/test",
            "POST",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type="Workflow",  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def update_workflow_state(self, body, workflow_id, **kwargs):  # noqa: E501
        """Update workflow variables  # noqa: E501

        Updates the workflow variables and triggers evaluation.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.update_workflow_state(body, workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param dict(str, object) body: (required)
        :param str workflow_id: (required)
        :return: Workflow
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.update_workflow_state_with_http_info(
                body, workflow_id, **kwargs
            )  # noqa: E501
        else:
            (data) = self.update_workflow_state_with_http_info(
                body, workflow_id, **kwargs
            )  # noqa: E501
            return data

    def update_workflow_state_with_http_info(
        self, body, workflow_id, **kwargs
    ):  # noqa: E501
        """Update workflow variables  # noqa: E501

        Updates the workflow variables and triggers evaluation.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.update_workflow_state_with_http_info(body, workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param dict(str, object) body: (required)
        :param str workflow_id: (required)
        :return: Workflow
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ["body", "workflow_id"]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method update_workflow_state" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'body' is set
        if "body" not in params or params["body"] is None:
            raise ValueError(
                "Missing the required parameter `body` when calling `update_workflow_state`"
            )  # noqa: E501
        # verify the required parameter 'workflow_id' is set
        if "workflow_id" not in params or params["workflow_id"] is None:
            raise ValueError(
                "Missing the required parameter `workflow_id` when calling `update_workflow_state`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "workflow_id" in params:
            path_params["workflowId"] = params["workflow_id"]  # noqa: E501

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        if "body" in params:
            body_params = params["body"]
        # HTTP header `Accept`
        header_params["Accept"] = self.api_client.select_header_accept(
            ["*/*"]
        )  # noqa: E501

        # HTTP header `Content-Type`
        header_params["Content-Type"] = (
            self.api_client.select_header_content_type(  # noqa: E501
                ["application/json"]
            )
        )  # noqa: E501

        # Authentication setting
        auth_settings = ["api_key"]  # noqa: E501

        return self.api_client.call_api(
            "/workflow/{workflowId}/variables",
            "POST",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type="Workflow",  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def upgrade_running_workflow_to_version(
        self, body, workflow_id, **kwargs
    ):  # noqa: E501
        """Upgrade running workflow to newer version  # noqa: E501

        Upgrade running workflow to newer version  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.upgrade_running_workflow_to_version(body, workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param UpgradeWorkflowRequest body: (required)
        :param str workflow_id: (required)
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.upgrade_running_workflow_to_version_with_http_info(
                body, workflow_id, **kwargs
            )  # noqa: E501
        else:
            (data) = self.upgrade_running_workflow_to_version_with_http_info(
                body, workflow_id, **kwargs
            )  # noqa: E501
            return data

    def upgrade_running_workflow_to_version_with_http_info(
        self, body, workflow_id, **kwargs
    ):  # noqa: E501
        """Upgrade running workflow to newer version  # noqa: E501

        Upgrade running workflow to newer version  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.upgrade_running_workflow_to_version_with_http_info(body, workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param UpgradeWorkflowRequest body: (required)
        :param str workflow_id: (required)
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ["body", "workflow_id"]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method upgrade_running_workflow_to_version" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'body' is set
        if "body" not in params or params["body"] is None:
            raise ValueError(
                "Missing the required parameter `body` when calling `upgrade_running_workflow_to_version`"
            )  # noqa: E501
        # verify the required parameter 'workflow_id' is set
        if "workflow_id" not in params or params["workflow_id"] is None:
            raise ValueError(
                "Missing the required parameter `workflow_id` when calling `upgrade_running_workflow_to_version`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "workflow_id" in params:
            path_params["workflowId"] = params["workflow_id"]  # noqa: E501

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        if "body" in params:
            body_params = params["body"]
        # HTTP header `Content-Type`
        header_params["Content-Type"] = (
            self.api_client.select_header_content_type(  # noqa: E501
                ["application/json"]
            )
        )  # noqa: E501

        # Authentication setting
        auth_settings = ["api_key"]  # noqa: E501

        return self.api_client.call_api(
            "/workflow/{workflowId}/upgrade",
            "POST",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type=None,  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def update_workflow_and_task_state(
        self, update_requesst, workflow_id, **kwargs
    ):  # noqa: E501
        request_id = str(uuid.uuid4())
        """Update a workflow state by updating variables or in progress task  # noqa: E501

        Updates the workflow variables, tasks and triggers evaluation.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.update_workflow_and_task_state(update_requesst, request_id, workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param WorkflowStateUpdate body: (required)
        :param str request_id: (required)
        :param str workflow_id: (required)
        :param str wait_until_task_ref:
        :param int wait_for_seconds:
        :return: WorkflowRun
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.update_workflow_and_task_state_with_http_info(
                update_requesst, request_id, workflow_id, **kwargs
            )  # noqa: E501
        else:
            (data) = self.update_workflow_and_task_state_with_http_info(
                update_requesst, request_id, workflow_id, **kwargs
            )  # noqa: E501
            return data

    def update_workflow_and_task_state_with_http_info(
        self, body, request_id, workflow_id, **kwargs
    ):  # noqa: E501
        """Update a workflow state by updating variables or in progress task  # noqa: E501

        Updates the workflow variables, tasks and triggers evaluation.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.update_workflow_and_task_state_with_http_info(body, request_id, workflow_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param WorkflowStateUpdate body: (required)
        :param str request_id: (required)
        :param str workflow_id: (required)
        :param str wait_until_task_ref:
        :param int wait_for_seconds:
        :return: WorkflowRun
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = [
            "body",
            "request_id",
            "workflow_id",
            "wait_until_task_ref",
            "wait_for_seconds",
        ]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method update_workflow_and_task_state" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'body' is set
        if "body" not in params or params["body"] is None:
            raise ValueError(
                "Missing the required parameter `body` when calling `update_workflow_and_task_state`"
            )  # noqa: E501
        # verify the required parameter 'request_id' is set
        if "request_id" not in params or params["request_id"] is None:
            raise ValueError(
                "Missing the required parameter `request_id` when calling `update_workflow_and_task_state`"
            )  # noqa: E501
        # verify the required parameter 'workflow_id' is set
        if "workflow_id" not in params or params["workflow_id"] is None:
            raise ValueError(
                "Missing the required parameter `workflow_id` when calling `update_workflow_and_task_state`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "workflow_id" in params:
            path_params["workflowId"] = params["workflow_id"]  # noqa: E501

        query_params = []
        if "request_id" in params:
            query_params.append(("requestId", params["request_id"]))  # noqa: E501
        if "wait_until_task_ref" in params:
            query_params.append(
                ("waitUntilTaskRef", params["wait_until_task_ref"])
            )  # noqa: E501
        if "wait_for_seconds" in params:
            query_params.append(
                ("waitForSeconds", params["wait_for_seconds"])
            )  # noqa: E501

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        if "body" in params:
            body_params = params["body"]
        # HTTP header `Accept`
        header_params["Accept"] = self.api_client.select_header_accept(
            ["*/*"]
        )  # noqa: E501

        # HTTP header `Content-Type`
        header_params["Content-Type"] = (
            self.api_client.select_header_content_type(  # noqa: E501
                ["application/json"]
            )
        )  # noqa: E501

        # Authentication setting
        auth_settings = ["api_key"]  # noqa: E501

        return self.api_client.call_api(
            "/workflow/{workflowId}/state",
            "POST",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type="WorkflowRun",  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )
