from abc import ABC, abstractmethod
from typing import Any

from ...memories.ltms.ltm import LTM
from ..workflow.context import BaseWorkflowContext
from ...base import BotBase


class Node(BotBase, ABC):
    """A Node is the minimal processing unit in a pipeline.
    All Nodes in a pipeline should share the same interface.
    """

    @abstractmethod
    def _run(self, args: BaseWorkflowContext, ltm: LTM) -> Any:
        """Run the Node."""

    async def _arun(self, args: BaseWorkflowContext, ltm: LTM) -> Any:
        """Run the Node."""
        raise NotImplementedError(
            f"Async run not implemented for {type(self).__name__} Node."
        )

    def run(self, args: BaseWorkflowContext, ltm: LTM):
        res = self._run(args, ltm)
        assert type(args) == type(res)
        self._forward(res, ltm)

    async def arun(self, args: BaseWorkflowContext, ltm: LTM):
        res = await self._arun(args, ltm)
        assert type(args) == type(res)
        await self._aforward(res, ltm)

    @abstractmethod
    def _forward(self, args: BaseWorkflowContext, ltm: LTM):
        """Process to next Node"""

    async def _aforward(self, args: BaseWorkflowContext, ltm: LTM):
        """Run the Node."""
        raise NotImplementedError(
            f"Async run not implemented for {type(self).__name__} Node."
        )
