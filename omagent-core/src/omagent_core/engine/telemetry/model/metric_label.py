from enum import Enum


class MetricLabel(str, Enum):
    ENTITY_NAME = "entityName"
    EXCEPTION = "exception"
    OPERATION = "operation"
    PAYLOAD_TYPE = "payload_type"
    TASK_TYPE = "taskType"
    WORKFLOW_TYPE = "workflowType"
    WORKFLOW_VERSION = "version"
