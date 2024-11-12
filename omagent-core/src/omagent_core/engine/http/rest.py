import io
import json
import re

import requests
from requests.adapters import HTTPAdapter
from six.moves.urllib.parse import urlencode
from urllib3 import Retry


class RESTResponse(io.IOBase):

    def __init__(self, resp):
        self.status = resp.status_code
        self.reason = resp.reason
        self.resp = resp
        self.headers = resp.headers

    def getheaders(self):
        return self.headers


class RESTClientObject(object):
    def __init__(self, connection=None):
        self.connection = connection or requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "DELETE"],  # all the methods that are supposed to be idempotent
        )
        self.connection.mount("https://", HTTPAdapter(max_retries=retry_strategy))
        self.connection.mount("http://", HTTPAdapter(max_retries=retry_strategy))

    def request(self, method, url, query_params=None, headers=None,
                body=None, post_params=None, _preload_content=True,
                _request_timeout=None):
        """Perform requests.

        :param method: http request method
        :param url: http request url
        :param query_params: query parameters in the url
        :param headers: http request headers
        :param body: request json body, for `application/json`
        :param post_params: request post parameters,
                            `application/x-www-form-urlencoded`
                            and `multipart/form-data`
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        """
        method = method.upper()
        assert method in ['GET', 'HEAD', 'DELETE', 'POST', 'PUT',
                          'PATCH', 'OPTIONS']

        if post_params and body:
            raise ValueError(
                "body parameter cannot be used with post_params parameter."
            )

        post_params = post_params or {}
        headers = headers or {}

        timeout = _request_timeout if _request_timeout is not None else (120, 120)

        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'

        try:
            # For `POST`, `PUT`, `PATCH`, `OPTIONS`, `DELETE`
            if method in ['POST', 'PUT', 'PATCH', 'OPTIONS', 'DELETE']:
                if query_params:
                    url += '?' + urlencode(query_params)
                if re.search('json', headers['Content-Type'], re.IGNORECASE) or isinstance(body, str):
                    request_body = '{}'
                    if body is not None:
                        request_body = json.dumps(body)
                        if isinstance(body, str):
                            request_body = request_body.strip('"')
                    r = self.connection.request(
                        method, url,
                        data=request_body,
                        timeout=timeout,
                        headers=headers
                    )
                else:
                    # Cannot generate the request from given parameters
                    msg = """Cannot prepare a request message for provided
                             arguments. Please check that your arguments match
                             declared content type."""
                    raise ApiException(status=0, reason=msg)
            # For `GET`, `HEAD`
            else:
                r = self.connection.request(
                    method, url,
                    params=query_params,
                    timeout=timeout,
                    headers=headers
                )
        except Exception as e:
            msg = "{0}\n{1}".format(type(e).__name__, str(e))
            raise ApiException(status=0, reason=msg)

        if _preload_content:
            r = RESTResponse(r)

        if r.status == 401 or r.status == 403:
            raise AuthorizationException(http_resp=r)

        if not 200 <= r.status <= 299:
            raise ApiException(http_resp=r)

        return r

    def GET(self, url, headers=None, query_params=None, _preload_content=True,
            _request_timeout=None):
        return self.request("GET", url,
                            headers=headers,
                            _preload_content=_preload_content,
                            _request_timeout=_request_timeout,
                            query_params=query_params)

    def HEAD(self, url, headers=None, query_params=None, _preload_content=True,
             _request_timeout=None):
        return self.request("HEAD", url,
                            headers=headers,
                            _preload_content=_preload_content,
                            _request_timeout=_request_timeout,
                            query_params=query_params)

    def OPTIONS(self, url, headers=None, query_params=None, post_params=None,
                body=None, _preload_content=True, _request_timeout=None):
        return self.request("OPTIONS", url,
                            headers=headers,
                            query_params=query_params,
                            post_params=post_params,
                            _preload_content=_preload_content,
                            _request_timeout=_request_timeout,
                            body=body)

    def DELETE(self, url, headers=None, query_params=None, body=None,
               _preload_content=True, _request_timeout=None):
        return self.request("DELETE", url,
                            headers=headers,
                            query_params=query_params,
                            _preload_content=_preload_content,
                            _request_timeout=_request_timeout,
                            body=body)

    def POST(self, url, headers=None, query_params=None, post_params=None,
             body=None, _preload_content=True, _request_timeout=None):
        return self.request("POST", url,
                            headers=headers,
                            query_params=query_params,
                            post_params=post_params,
                            _preload_content=_preload_content,
                            _request_timeout=_request_timeout,
                            body=body)

    def PUT(self, url, headers=None, query_params=None, post_params=None,
            body=None, _preload_content=True, _request_timeout=None):
        return self.request("PUT", url,
                            headers=headers,
                            query_params=query_params,
                            post_params=post_params,
                            _preload_content=_preload_content,
                            _request_timeout=_request_timeout,
                            body=body)

    def PATCH(self, url, headers=None, query_params=None, post_params=None,
              body=None, _preload_content=True, _request_timeout=None):
        return self.request("PATCH", url,
                            headers=headers,
                            query_params=query_params,
                            post_params=post_params,
                            _preload_content=_preload_content,
                            _request_timeout=_request_timeout,
                            body=body)


class ApiException(Exception):

    def __init__(self, status=None, reason=None, http_resp=None, body=None):
        if http_resp:
            self.status = http_resp.status
            self.code = http_resp.status
            self.reason = http_resp.reason
            self.body = http_resp.resp.text
            try:
                if http_resp.resp.text:
                    error = json.loads(http_resp.resp.text)
                    self.message = error['message']
                else:
                    self.message = http_resp.resp.text
            except Exception as e:
                self.message = http_resp.resp.text
            self.headers = http_resp.getheaders()
        else:
            self.status = status
            self.code = status
            self.reason = reason
            self.body = body
            self.message = body
            self.headers = None

    def __str__(self):
        """Custom error messages for exception"""
        error_message = "({0})\n" \
                        "Reason: {1}\n".format(self.status, self.reason)
        if self.headers:
            error_message += "HTTP response headers: {0}\n".format(
                self.headers)

        if self.body:
            error_message += "HTTP response body: {0}\n".format(self.body)

        return error_message

    def is_not_found(self) -> bool:
        return self.code == 404

class AuthorizationException(ApiException):
    def __init__(self, status=None, reason=None, http_resp=None, body=None):
        try:
            data = json.loads(http_resp.resp.text)
            if 'error' in data:
                self._error_code = data['error']
            else:
                self._error_code = ''
        except (Exception):
            self._error_code = ''
        super().__init__(status, reason, http_resp, body)

    @property
    def error_code(self):
        return self._error_code

    @property
    def status_code(self):
        return self.status

    @property
    def token_expired(self) -> bool:
        return self._error_code == 'EXPIRED_TOKEN'

    @property
    def invalid_token(self) -> bool:
        return self._error_code == 'INVALID_TOKEN'

    def __str__(self):
        """Custom error messages for exception"""
        error_message = f'authorization error: {self._error_code}.  status_code: {self.status}, reason: {self.reason}'

        if self.headers:
            error_message += f', headers: {self.headers}'

        if self.body:
            error_message += f', response: {self.body}'

        return error_message
