from enum import Enum


class MetricDocumentation(str, Enum):
    EXTERNAL_PAYLOAD_USED = "Incremented each time external payload storage is used"
    TASK_ACK_ERROR = "Task ack has encountered an exception"
    TASK_ACK_FAILED = "Task ack failed"
    TASK_EXECUTE_ERROR = "Execution error"
    TASK_EXECUTE_TIME = "Time to execute a task"
    TASK_EXECUTION_QUEUE_FULL = "Counter to record execution queue has saturated"
    TASK_PAUSED = "Counter for number of times the task has been polled, when the worker has been paused"
    TASK_POLL = "Incremented each time polling is done"
    TASK_POLL_ERROR = "Client error when polling for a task queue"
    TASK_POLL_TIME = "Time to poll for a batch of tasks"
    TASK_RESULT_SIZE = "Records output payload size of a task"
    TASK_UPDATE_ERROR = "Task status cannot be updated back to server"
    THREAD_UNCAUGHT_EXCEPTION = "thread_uncaught_exceptions"
    WORKFLOW_START_ERROR = "Counter for workflow start errors"
    WORKFLOW_INPUT_SIZE = "Records input payload size of a workflow"
