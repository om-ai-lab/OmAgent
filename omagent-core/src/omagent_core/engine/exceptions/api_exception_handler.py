import json

from omagent_core.engine.exceptions.api_error import APIError, APIErrorCode
from omagent_core.engine.http.rest import ApiException

STATUS_TO_MESSAGE_DEFAULT_MAPPING = {
    400: "Invalid request",
    403: "Access forbidden",
    404: "Resource not found",
    408: "Request timed out",
    409: "Resource exists already",
}


def api_exception_handler(function):
    def inner_function(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except ApiException as e:

            if e.status == 404:
                code = APIErrorCode.NOT_FOUND
            elif e.status == 403:
                code = APIErrorCode.FORBIDDEN
            elif e.status == 409:
                code = APIErrorCode.CONFLICT
            elif e.status == 400:
                code = APIErrorCode.BAD_REQUEST
            elif e.status == 408:
                code = APIErrorCode.REQUEST_TIMEOUT
            else:
                code = APIErrorCode.UNKNOWN

            message = STATUS_TO_MESSAGE_DEFAULT_MAPPING[e.status]

            try:
                if e.body:
                    error = json.loads(e.body)
                    message = error["message"]
            except ValueError:
                message = e.body

            finally:
                raise APIError(code, message)

    return inner_function


def for_all_methods(decorator, exclude=[]):
    def decorate(cls):
        for attr in cls.__dict__:
            if callable(getattr(cls, attr)) and attr not in exclude:
                setattr(cls, attr, decorator(getattr(cls, attr)))
        return cls

    return decorate
