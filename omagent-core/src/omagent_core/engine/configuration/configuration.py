import logging
import os
import time
from typing import Any, Optional

from omagent_core.engine.configuration.settings.authentication_settings import \
    AuthenticationSettings
from pydantic import Field
from pydantic_settings import BaseSettings

TEMPLATE_CONFIG = {
    "name": "Configuration",
    "base_url": {
        "value": "http://localhost:8080",
        "description": "The Conductor Server API endpoint",
        "env_var": "CONDUCTOR_SERVER_URL",
    },
    "auth_key": {
        "value": None,
        "description": "The authorization key",
        "env_var": "AUTH_KEY",
    },
    "auth_secret": {
        "value": None,
        "description": "The authorization secret",
        "env_var": "CONDUCTOR_AUTH_SECRET",
    },
    "auth_token_ttl_min": {
        "value": 45,
        "description": "The authorization token refresh interval in minutes.",
        "env_var": "AUTH_TOKEN_TTL_MIN",
    },
    "debug": {"value": False, "description": "Debug mode", "env_var": "DEBUG"},
}


class Configuration(BaseSettings):
    class Config:
        """Configuration for this pydantic object."""

        extra = "allow"

    base_url: str = Field(
        default="http://localhost:8080", description="The Conductor Server API endpoint"
    )
    auth_key: Optional[str] = Field(default=None, description="The authorization key")
    auth_secret: Optional[str] = Field(
        default=None,
        description="The authorization secret",
    )
    auth_token_ttl_min: int = Field(
        default=45, description="The authorization token refresh interval in minutes."
    )
    debug: bool = Field(default=False, description="Debug mode")

    def model_post_init(self, __context: Any) -> None:
        self.__log_level = logging.DEBUG if self.debug else logging.INFO
        self.AUTH_TOKEN = None
        self.temp_folder_path = None
        self.host = self.base_url + "/api"
        self.__ui_host = self.host.replace("8080/api", "5000")
        if self.auth_key and self.auth_secret:
            self.authentication_settings = AuthenticationSettings(
                key_id=self.auth_key, key_secret=self.auth_secret
            )
        else:
            self.authentication_settings = None

        # Log format
        self.logger_format = "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"

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
        self.safe_chars_for_path_param = ""

        # Provide an alterative to requests.Session() for HTTP connection.
        self.http_connection = None

        # not updated yet
        self.token_update_time = 0
        self.auth_token_ttl_msec = self.auth_token_ttl_min * 60 * 1000

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

    def apply_logging_config(self, log_format: str = None, level=None):
        if log_format is None:
            log_format = self.logger_format
        if level is None:
            level = self.__log_level
        logging.basicConfig(format=log_format, level=level)

    @staticmethod
    def get_logging_formatted_name(name):
        return f"[{os.getpid()}] {name}"

    def update_token(self, token: str) -> None:
        self.AUTH_TOKEN = token
        self.token_update_time = round(time.time() * 1000)
