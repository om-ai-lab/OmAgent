from abc import ABC, abstractmethod

from omagent_core.base import BotBase


class InputBase(BotBase, ABC):

    class Config:
        """Configuration for this pydantic object."""

        arbitrary_types_allowed = True
        extra = "allow"

    @abstractmethod
    def read_input(self, **kwargs):
        pass
