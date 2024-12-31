from __future__ import absolute_import

import re  # noqa: F401

# python 2 and python 3 compatibility library
import six
from omagent_core.engine.http.api_client import ApiClient


class EventResourceApi(object):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    Ref: https://github.com/swagger-api/swagger-codegen
    """

    def __init__(self, api_client=None):
        if api_client is None:
            api_client = ApiClient()
        self.api_client = api_client

    def add_event_handler(self, body, **kwargs):  # noqa: E501
        """Add a new event handler.  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.add_event_handler(body, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param EventHandler body: (required)
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.add_event_handler_with_http_info(body, **kwargs)  # noqa: E501
        else:
            (data) = self.add_event_handler_with_http_info(body, **kwargs)  # noqa: E501
            return data

    def add_event_handler_with_http_info(self, body, **kwargs):  # noqa: E501
        """Add a new event handler.  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.add_event_handler_with_http_info(body, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param EventHandler body: (required)
        :return: None
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
                    " to method add_event_handler" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'body' is set
        if "body" not in params or params["body"] is None:
            raise ValueError(
                "Missing the required parameter `body` when calling `add_event_handler`"
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
        # HTTP header `Content-Type`
        header_params["Content-Type"] = (
            self.api_client.select_header_content_type(  # noqa: E501
                ["application/json"]
            )
        )  # noqa: E501

        # Authentication setting
        auth_settings = []  # noqa: E501

        return self.api_client.call_api(
            "/event",
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

    def delete_queue_config(self, queue_type, queue_name, **kwargs):  # noqa: E501
        """Delete queue config by name  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.delete_queue_config(queue_type, queue_name, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str queue_type: (required)
        :param str queue_name: (required)
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.delete_queue_config_with_http_info(
                queue_type, queue_name, **kwargs
            )  # noqa: E501
        else:
            (data) = self.delete_queue_config_with_http_info(
                queue_type, queue_name, **kwargs
            )  # noqa: E501
            return data

    def delete_queue_config_with_http_info(
        self, queue_type, queue_name, **kwargs
    ):  # noqa: E501
        """Delete queue config by name  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.delete_queue_config_with_http_info(queue_type, queue_name, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str queue_type: (required)
        :param str queue_name: (required)
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ["queue_type", "queue_name"]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method delete_queue_config" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'queue_type' is set
        if "queue_type" not in params or params["queue_type"] is None:
            raise ValueError(
                "Missing the required parameter `queue_type` when calling `delete_queue_config`"
            )  # noqa: E501
        # verify the required parameter 'queue_name' is set
        if "queue_name" not in params or params["queue_name"] is None:
            raise ValueError(
                "Missing the required parameter `queue_name` when calling `delete_queue_config`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "queue_type" in params:
            path_params["queueType"] = params["queue_type"]  # noqa: E501
        if "queue_name" in params:
            path_params["queueName"] = params["queue_name"]  # noqa: E501

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # Authentication setting
        auth_settings = []  # noqa: E501

        return self.api_client.call_api(
            "/event/queue/config/{queueType}/{queueName}",
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

    def get_event_handlers(self, **kwargs):  # noqa: E501
        """Get all the event handlers  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_event_handlers(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :return: list[EventHandler]
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.get_event_handlers_with_http_info(**kwargs)  # noqa: E501
        else:
            (data) = self.get_event_handlers_with_http_info(**kwargs)  # noqa: E501
            return data

    def get_event_handlers_with_http_info(self, **kwargs):  # noqa: E501
        """Get all the event handlers  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_event_handlers_with_http_info(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :return: list[EventHandler]
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = []  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method get_event_handlers" % key
                )
            params[key] = val
        del params["kwargs"]

        collection_formats = {}

        path_params = {}

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params["Accept"] = self.api_client.select_header_accept(
            ["*/*"]
        )  # noqa: E501

        # Authentication setting
        auth_settings = []  # noqa: E501

        return self.api_client.call_api(
            "/event",
            "GET",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type="list[EventHandler]",  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def get_event_handlers_for_event(self, event, **kwargs):  # noqa: E501
        """Get event handlers for a given event  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_event_handlers_for_event(event, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str event: (required)
        :param bool active_only:
        :return: list[EventHandler]
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.get_event_handlers_for_event_with_http_info(
                event, **kwargs
            )  # noqa: E501
        else:
            (data) = self.get_event_handlers_for_event_with_http_info(
                event, **kwargs
            )  # noqa: E501
            return data

    def get_event_handlers_for_event_with_http_info(
        self, event, **kwargs
    ):  # noqa: E501
        """Get event handlers for a given event  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_event_handlers_for_event_with_http_info(event, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str event: (required)
        :param bool active_only:
        :return: list[EventHandler]
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ["event", "active_only"]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method get_event_handlers_for_event" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'event' is set
        if "event" not in params or params["event"] is None:
            raise ValueError(
                "Missing the required parameter `event` when calling `get_event_handlers_for_event`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "event" in params:
            path_params["event"] = params["event"]  # noqa: E501

        query_params = []
        if "active_only" in params:
            query_params.append(("activeOnly", params["active_only"]))  # noqa: E501

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params["Accept"] = self.api_client.select_header_accept(
            ["*/*"]
        )  # noqa: E501

        # Authentication setting
        auth_settings = []  # noqa: E501

        return self.api_client.call_api(
            "/event/{event}",
            "GET",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type="list[EventHandler]",  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def get_queue_config(self, queue_type, queue_name, **kwargs):  # noqa: E501
        """Get queue config by name  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_queue_config(queue_type, queue_name, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str queue_type: (required)
        :param str queue_name: (required)
        :return: dict(str, object)
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.get_queue_config_with_http_info(
                queue_type, queue_name, **kwargs
            )  # noqa: E501
        else:
            (data) = self.get_queue_config_with_http_info(
                queue_type, queue_name, **kwargs
            )  # noqa: E501
            return data

    def get_queue_config_with_http_info(
        self, queue_type, queue_name, **kwargs
    ):  # noqa: E501
        """Get queue config by name  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_queue_config_with_http_info(queue_type, queue_name, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str queue_type: (required)
        :param str queue_name: (required)
        :return: dict(str, object)
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ["queue_type", "queue_name"]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method get_queue_config" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'queue_type' is set
        if "queue_type" not in params or params["queue_type"] is None:
            raise ValueError(
                "Missing the required parameter `queue_type` when calling `get_queue_config`"
            )  # noqa: E501
        # verify the required parameter 'queue_name' is set
        if "queue_name" not in params or params["queue_name"] is None:
            raise ValueError(
                "Missing the required parameter `queue_name` when calling `get_queue_config`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "queue_type" in params:
            path_params["queueType"] = params["queue_type"]  # noqa: E501
        if "queue_name" in params:
            path_params["queueName"] = params["queue_name"]  # noqa: E501

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params["Accept"] = self.api_client.select_header_accept(
            ["*/*"]
        )  # noqa: E501

        # Authentication setting
        auth_settings = []  # noqa: E501

        return self.api_client.call_api(
            "/event/queue/config/{queueType}/{queueName}",
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

    def get_queue_names(self, **kwargs):  # noqa: E501
        """Get all queue configs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_queue_names(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :return: dict(str, str)
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.get_queue_names_with_http_info(**kwargs)  # noqa: E501
        else:
            (data) = self.get_queue_names_with_http_info(**kwargs)  # noqa: E501
            return data

    def get_queue_names_with_http_info(self, **kwargs):  # noqa: E501
        """Get all queue configs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_queue_names_with_http_info(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :return: dict(str, str)
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = []  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method get_queue_names" % key
                )
            params[key] = val
        del params["kwargs"]

        collection_formats = {}

        path_params = {}

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params["Accept"] = self.api_client.select_header_accept(
            ["*/*"]
        )  # noqa: E501

        # Authentication setting
        auth_settings = []  # noqa: E501

        return self.api_client.call_api(
            "/event/queue/config",
            "GET",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type="dict(str, str)",  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )

    def put_queue_config(self, body, queue_type, queue_name, **kwargs):  # noqa: E501
        """Create or update queue config by name  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.put_queue_config(body, queue_type, queue_name, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str body: (required)
        :param str queue_type: (required)
        :param str queue_name: (required)
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.put_queue_config_with_http_info(
                body, queue_type, queue_name, **kwargs
            )  # noqa: E501
        else:
            (data) = self.put_queue_config_with_http_info(
                body, queue_type, queue_name, **kwargs
            )  # noqa: E501
            return data

    def put_queue_config_with_http_info(
        self, body, queue_type, queue_name, **kwargs
    ):  # noqa: E501
        """Create or update queue config by name  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.put_queue_config_with_http_info(body, queue_type, queue_name, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str body: (required)
        :param str queue_type: (required)
        :param str queue_name: (required)
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ["body", "queue_type", "queue_name"]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method put_queue_config" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'body' is set
        if "body" not in params or params["body"] is None:
            raise ValueError(
                "Missing the required parameter `body` when calling `put_queue_config`"
            )  # noqa: E501
        # verify the required parameter 'queue_type' is set
        if "queue_type" not in params or params["queue_type"] is None:
            raise ValueError(
                "Missing the required parameter `queue_type` when calling `put_queue_config`"
            )  # noqa: E501
        # verify the required parameter 'queue_name' is set
        if "queue_name" not in params or params["queue_name"] is None:
            raise ValueError(
                "Missing the required parameter `queue_name` when calling `put_queue_config`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "queue_type" in params:
            path_params["queueType"] = params["queue_type"]  # noqa: E501
        if "queue_name" in params:
            path_params["queueName"] = params["queue_name"]  # noqa: E501

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
        auth_settings = []  # noqa: E501

        return self.api_client.call_api(
            "/event/queue/config/{queueType}/{queueName}",
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

    def remove_event_handler_status(self, name, **kwargs):  # noqa: E501
        """Remove an event handler  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.remove_event_handler_status(name, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str name: (required)
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.remove_event_handler_status_with_http_info(
                name, **kwargs
            )  # noqa: E501
        else:
            (data) = self.remove_event_handler_status_with_http_info(
                name, **kwargs
            )  # noqa: E501
            return data

    def remove_event_handler_status_with_http_info(self, name, **kwargs):  # noqa: E501
        """Remove an event handler  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.remove_event_handler_status_with_http_info(name, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str name: (required)
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ["name"]  # noqa: E501
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()
        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method remove_event_handler_status" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'name' is set
        if "name" not in params or params["name"] is None:
            raise ValueError(
                "Missing the required parameter `name` when calling `remove_event_handler_status`"
            )  # noqa: E501

        collection_formats = {}

        path_params = {}
        if "name" in params:
            path_params["name"] = params["name"]  # noqa: E501

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # Authentication setting
        auth_settings = []  # noqa: E501

        return self.api_client.call_api(
            "/event/{name}",
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

    def update_event_handler(self, body, **kwargs):  # noqa: E501
        """Update an existing event handler.  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.update_event_handler(body, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param EventHandler body: (required)
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.update_event_handler_with_http_info(
                body, **kwargs
            )  # noqa: E501
        else:
            (data) = self.update_event_handler_with_http_info(
                body, **kwargs
            )  # noqa: E501
            return data

    def update_event_handler_with_http_info(self, body, **kwargs):  # noqa: E501
        """Update an existing event handler.  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.update_event_handler_with_http_info(body, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param EventHandler body: (required)
        :return: None
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
                    " to method update_event_handler" % key
                )
            params[key] = val
        del params["kwargs"]
        # verify the required parameter 'body' is set
        if "body" not in params or params["body"] is None:
            raise ValueError(
                "Missing the required parameter `body` when calling `update_event_handler`"
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
        # HTTP header `Content-Type`
        header_params["Content-Type"] = (
            self.api_client.select_header_content_type(  # noqa: E501
                ["application/json"]
            )
        )  # noqa: E501

        # Authentication setting
        auth_settings = []  # noqa: E501

        return self.api_client.call_api(
            "/event",
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
