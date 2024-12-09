from enum import Enum


class AccessKeyStatus(str, Enum):
    ACTIVE = "ACTIVE",
    INACTIVE = "INACTIVE"
