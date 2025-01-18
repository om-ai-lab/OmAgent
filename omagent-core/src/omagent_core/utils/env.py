import os
from distutils.util import strtobool


class EnvVar(object):
    APP_NAME = "OmAgent"

    IS_DEBUG = strtobool(os.environ.get("IS_DEBUG", "false"))

    STOP_AFTER_DELAY = int(
        os.environ.get("STOP_AFTER_DELAY", 20)
    )  # LLM will stop when the time from the first attempt >= limit
    STOP_AFTER_ATTEMPT = int(os.environ.get("STOP_AFTER_ATTEMPT", 5))  # LLM retry times
    LLM_CACHE_NUM = int(os.environ.get("LLM_CACHE_NUM", 500))  # LLM result cache number

    MAX_NODE_RETRY = int(os.environ.get("MAX_NODE_RETRY", 3))

    @classmethod
    def update(cls, key, value):
        setattr(cls, key, value)

    @classmethod
    def get(cls, key, default=None):
        return getattr(cls, key, default)
