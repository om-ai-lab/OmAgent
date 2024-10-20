from abc import ABC, abstractmethod
from typing import Optional, Union

from pydantic import field_validator

from ...memories.ltms.ltm import LTM
from ..workflow.context import BaseWorkflowContext
from ...utils.registry import registry
from .base import Node


class BaseProcessor(Node, ABC):
    next_step: Optional[Node] = None

    @field_validator("next_step", mode="before")
    @classmethod
    def init_next_step(cls, next_step: Union[Node, None]) -> Union[Node, None]:
        if isinstance(next_step, dict):
            return registry.get_node(next_step["name"])(**next_step)
        elif isinstance(next_step, Node):
            return next_step
        elif not next_step:
            return None
        else:
            raise ValueError(
                "Wrong next step type {}, should be one of [Node, dict, None] in node [{}]".format(
                    type(next_step), cls.__name__
                )
            )

    @abstractmethod
    def _run(self, args: BaseWorkflowContext, ltm: LTM) -> BaseWorkflowContext:
        """Run the Node."""

    async def _arun(self, args: BaseWorkflowContext, ltm: LTM) -> BaseWorkflowContext:
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

    def _forward(self, args: BaseWorkflowContext, ltm: LTM):
        """Process to next Node"""
        if not self.next_step:
            self.callback.finish()
            return
        else:
            self.next_step.run(args, ltm)

    async def _aforward(self, args: BaseWorkflowContext, ltm: LTM):
        """Process to next Node"""
        if not self.next_step:
            self.callback.finish()
            return
        else:
            await self.next_step.arun(args, ltm)
