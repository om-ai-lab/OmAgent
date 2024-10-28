import logging
import os
import time

from omagent_core.engine.configuration.settings.authentication_settings import AuthenticationSettings


class Configuration:
    AUTH_TOKEN = None

    def __init__(
            self,
            base_url: str = None,
            debug: bool = False,
            authentication_settings: AuthenticationSettings = None,
            server_api_url: str = None,
            auth_token_ttl_min: int = 45
    ):
        if server_api_url is not None:
            self.host = server_api_url
        elif base_url is not None:
            self.host = base_url + '/api'
        else:
            self.host = os.getenv('CONDUCTOR_SERVER_URL')

        if self.host is None or self.host == '':
            self.host = 'http://localhost:8080/api'

        self.temp_folder_path = None
        self.__ui_host = os.getenv('CONDUCTOR_UI_SERVER_URL')
        if self.__ui_host is None:
            self.__ui_host = self.host.replace('8080/api', '5000')

        if authentication_settings is not None:
            self.authentication_settings = authentication_settings
        else:
            key = os.getenv('CONDUCTOR_AUTH_KEY')
            secret = os.getenv('CONDUCTOR_AUTH_SECRET')
            if key is not None and secret is not None:
                self.authentication_settings = AuthenticationSettings(key_id=key, key_secret=secret)
            else:
                self.authentication_settings = None


        # Debug switch
        self.debug = debug
        # Log format
        self.logger_format = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'

        # SSL/TLS verification
        # Set this to false to skip verifying SSL certificate when calling API
        # from https server.
        self.verify_ssl = True
        # Set this to customize the certificate file to verify the peer.
        self.ssl_ca_cert = None
        # client certificate file
        self.cert_file = None
        # client key file
        self.key_file = None
        # Set this to True/False to enable/disable SSL hostname verification.
        self.assert_hostname = None

        # Proxy URL
        self.proxy = None
        # Safe chars for path_param
        self.safe_chars_for_path_param = ''

        # Provide an alterative to requests.Session() for HTTP connection.
        self.http_connection = None

        # not updated yet
        self.token_update_time = 0
        self.auth_token_ttl_msec = auth_token_ttl_min * 60 * 1000

    @property
    def debug(self):
        """Debug status

        :param value: The debug status, True or False.
        :type: bool
        """
        return self.__debug

    @debug.setter
    def debug(self, value):
        """Debug status

        :param value: The debug status, True or False.
        :type: bool
        """
        self.__debug = value
        if self.__debug:
            self.__log_level = logging.DEBUG
        else:
            self.__log_level = logging.INFO

    @property
    def logger_format(self):
        """The logger format.

        The logger_formatter will be updated when sets logger_format.

        :param value: The format string.
        :type: str
        """
        return self.__logger_format

    @logger_format.setter
    def logger_format(self, value):
        """The logger format.

        The logger_formatter will be updated when sets logger_format.

        :param value: The format string.
        :type: str
        """
        self.__logger_format = value

    @property
    def log_level(self):
        """The log level.

        The log_level will be updated when sets logger_format.

        :param value: The format string.
        :type: str
        """
        return self.__log_level

    @property
    def ui_host(self):
        """

        The log_level will be updated when sets logger_format.

        :param value: The format string.
        :type: str
        """
        return self.__ui_host

    def apply_logging_config(self, log_format : str = None, level = None):
        if log_format is None:
            log_format = self.logger_format
        if level is None:
            level = self.__log_level
        logging.basicConfig(
            format=log_format,
            level=level
        )

    @staticmethod
    def get_logging_formatted_name(name):
        return f'[{os.getpid()}] {name}'

    def update_token(self, token: str) -> None:
        self.AUTH_TOKEN = token
        self.token_update_time = round(time.time() * 1000)
