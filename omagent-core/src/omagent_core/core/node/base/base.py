from abc import ABC, abstractmethod
from typing import Any

from ....handlers.data_handler.ltm import LTM
from ....schemas.base import BaseInterface
from ...base import BotBase


class Node(BotBase, ABC):
    """A Node is the minimal processing unit in a pipeline.
    All Nodes in a pipeline should share the same interface.
    """

    @abstractmethod
    def _run(self, args: BaseInterface, ltm: LTM) -> Any:
        """Run the Node."""

    async def _arun(self, args: BaseInterface, ltm: LTM) -> Any:
        """Run the Node."""
        raise NotImplementedError(
            f"Async run not implemented for {type(self).__name__} Node."
        )

    def run(self, args: BaseInterface, ltm: LTM):
        res = self._run(args, ltm)
        assert type(args) == type(res)
        self._forward(res, ltm)

    async def arun(self, args: BaseInterface, ltm: LTM):
        res = await self._arun(args, ltm)
        assert type(args) == type(res)
        await self._aforward(res, ltm)

    @abstractmethod
    def _forward(self, args: BaseInterface, ltm: LTM):
        """Process to next Node"""

    async def _aforward(self, args: BaseInterface, ltm: LTM):
        """Run the Node."""
        raise NotImplementedError(
            f"Async run not implemented for {type(self).__name__} Node."
        )
