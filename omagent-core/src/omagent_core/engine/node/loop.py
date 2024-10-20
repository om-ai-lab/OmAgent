from abc import ABC
from typing import Callable, Dict, Union

from pydantic import field_validator
from pydantic._internal._model_construction import ModelMetaclass

from ...memories.ltms.ltm import LTM
from ..workflow.context import BaseWorkflowContext
from ...utils.registry import registry
from .base import Node
from .processor import BaseProcessor


class LoopMeta(ModelMetaclass):
    def __init__(cls, name, bases, attrs):
        abstract_methods = [
            name
            for name, value in attrs.items()
            if isinstance(value, Callable)
            if name in ("pre_loop_exit", "post_loop_exit")
        ]
        if not abstract_methods:
            raise ValueError(
                f"At least one loop exit method must be implemented in {name}"
            )
        super().__init__(name, bases, attrs)


class BaseLoop(BaseProcessor, ABC, metaclass=LoopMeta):
    """A special Processor that used to deal with loop logic. The loop_body will keep running until one of loop_exit return True."""

    loop_body: Node

    @field_validator("loop_body", mode="before")
    @classmethod
    def init_loop_body(cls, loop_body: Union[Node, Dict]) -> Node:
        if isinstance(loop_body, dict):
            return registry.get_node(loop_body["name"])(**loop_body)
        elif isinstance(loop_body, Node):
            return loop_body
        else:
            raise ValueError(
                "Wrong loop_body type {}, should be Node or dict in loop [{}]".format(
                    type(loop_body), cls.__name__
                )
            )

    def run(self, args: BaseWorkflowContext, ltm: LTM):
        while not self.pre_loop_exit(args, ltm):
            self.callback.send_block(self.name)
            self.loop_body.run(args, ltm)
            if self.post_loop_exit(args, ltm):
                break

        self._forward(args, ltm)

    async def arun(self, args: BaseWorkflowContext, ltm: LTM):
        while not self.pre_loop_exit(args, ltm):
            await self.loop_body.arun(args, ltm)
            if self.post_loop_exit(args, ltm):
                break

        await self._aforward(args, ltm)

    def pre_loop_exit(self, args: BaseWorkflowContext, ltm: LTM) -> bool:
        """This function is used to set a breakpoint for the loop before every time the loop_body is executed.

        Returns:
            bool: True to break the loop, False to continue.
        """
        return False

    def post_loop_exit(self, args: BaseWorkflowContext, ltm: LTM) -> bool:
        """This function is used to set a breakpoint for the loop after every time the loop_body is executed.

        Returns:
            bool: True to break the loop, False to continue.
        """
        return False

    def _run(self, args: BaseWorkflowContext, ltm: LTM) -> BaseWorkflowContext:
        pass
