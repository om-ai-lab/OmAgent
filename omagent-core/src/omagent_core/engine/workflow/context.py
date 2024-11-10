from pydantic import BaseModel
from abc import ABC
from typing import Any, Dict, Optional

from ..task.agent_task import TaskNode

class BaseWorkflowContext(BaseModel, ABC):
    class Config:
        """Configuration for this pydantic object."""

        extra = "allow"
        arbitrary_types_allowed = True

    last_output: Any = None
    kwargs: dict = {}
    task: TaskNode