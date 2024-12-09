from enum import Enum


class APIErrorCode(str, Enum):
    NOT_FOUND = 404,
    FORBIDDEN = 403
    CONFLICT = 409
    BAD_REQUEST = 400
    REQUEST_TIMEOUT = 408
    UNKNOWN = 0


class APIError(Exception):

    def __init__(self, status=None, reason=None, http_resp=None, body=None):
        super().__init__(status, reason, http_resp, body)

    def __str__(self):
        return "APIError: code={} message={}".format(self.code, self.message)
