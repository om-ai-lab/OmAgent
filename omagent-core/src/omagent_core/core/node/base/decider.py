from abc import ABC, abstractmethod
from typing import Dict, Tuple, Union

from pydantic import field_validator

from ....handlers import VQLError
from ....handlers.data_handler.ltm import LTM
from ....schemas.base import BaseInterface
from ....utils.registry import registry
from .base import Node


class BaseDecider(Node, ABC):
    """A Node is the minimal processing unit in a pipeline.
    All Nodes in a pipeline should share the same interface.
    """

    next_step: Dict[str, Union[Node, Dict, None]] = {}

    @field_validator("next_step", mode="before")
    @classmethod
    def init_next_step(cls, next_step: Dict[str, Union[Node, Dict]]) -> Dict[str, Node]:
        if not next_step:
            return {}
        elif not isinstance(next_step, dict):
            raise ValueError("Wrong next step type, should be dict")
        for key, step in next_step.items():
            if isinstance(step, dict):
                next_step[key] = registry.get_node(step["name"])(**step)
            elif isinstance(step, Node):
                pass
            elif step is None:
                pass
            else:
                raise ValueError(
                    "Wrong next step type {}, should be one of the following [dict, Node, None] in node [{}]".format(
                        type(step), cls.__name__
                    )
                )
        return next_step

    @abstractmethod
    def _run(self, args: BaseInterface, ltm: LTM) -> Tuple[BaseInterface, str]:
        """Run the Node."""

    async def _arun(self, args: BaseInterface, ltm: LTM) -> Tuple[BaseInterface, str]:
        """Run the Node."""
        raise NotImplementedError(
            f"Async run not implemented for {type(self).__name__} Node."
        )

    def run(self, args: BaseInterface, ltm: LTM):
        res, next_key = self._run(args, ltm)
        assert type(args) == type(res)
        self._forward(next_key, res, ltm)

    async def arun(self, args: BaseInterface, ltm: LTM):
        res, next_key = await self._arun(args, ltm)
        assert type(args) == type(res)
        await self._aforward(next_key, res, ltm)

    def _forward(self, next_key: str, args: BaseInterface, ltm: LTM):
        """Process to next Node"""
        if not self.next_step:
            self.callback.finish()
            return
        else:
            next_step = self.next_step.get(next_key, "not found")
            if next_step is None:
                self.callback.finish()
                return
            if next_step == "not found":
                raise VQLError(
                    500,
                    detail="Wrong next step key [{}], should be one of the following {}".format(
                        next_key, list(self.next_step.keys())
                    ),
                )
            next_step.run(args, ltm)

    async def _aforward(self, next_key: str, args: BaseInterface, ltm: LTM):
        """Process to next Node"""
        if not self.next_step:
            self.callback.finish()
            return
        else:
            next_step = self.next_step.get(next_key, "not found")
            if next_step is None:
                self.callback.finish()
                return
            if next_step == "not found":
                raise VQLError(
                    500,
                    detail="Wrong next step key [{}], should be one of the following {}".format(
                        next_key, list(self.next_step.keys())
                    ),
                )
            await next_step.arun(args, ltm)
