from enum import Enum


class TimeoutPolicy(str, Enum):
    TIME_OUT_WORKFLOW = "TIME_OUT_WF",
    ALERT_ONLY = "ALERT_ONLY",
