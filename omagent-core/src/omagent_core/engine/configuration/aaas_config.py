import logging
import os
import time
from typing import Any, Optional

from omagent_core.engine.configuration.settings.authentication_settings import \
    AuthenticationSettings
from pydantic import Field
from pydantic_settings import BaseSettings

AAAS_TEMPLATE_CONFIG = {
    "name": "AaasConfig",
    "base_url": {
        "value": "http://localhost:30002",
        "description": "The aaas task server API endpoint",
        "env_var": "AAAS_TASK_SERVER_URL",
    },
    "token": {
        "value": None,
        "description": "The authorization token",
        "env_var": "AAAS_TOKEN",
    },
    "enable": {
        "value": True,
        "description": "Whether to enable the aaas task server",
        "env_var": "AAAS_ENABLE",
    }
}


class AaasConfig(BaseSettings):
    class Config:
        """Configuration for this pydantic object."""

        extra = "allow"

    base_url: str = Field(
        default="http://localhost:30002", description="The aaas task server API endpoint"
    )
    token: Optional[str] = Field(
        default=None,
        description="The authorization token",
    )
    enable: bool = Field(
        default=True,
        description="Whether to enable the aaas task server",
    )

    def model_post_init(self, __context: Any) -> None:
        self.host = self.base_url + "/api"
