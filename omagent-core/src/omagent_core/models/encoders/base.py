from abc import ABC, abstractmethod
from typing import List

from ...base import BotBase
from ...utils.general import chunks


class EncoderBase(BotBase, ABC):
    endpoint: str
    dim: int  # Dimension of the vector
    batch_size: int = 20

    @abstractmethod
    def _infer(self, data: List[str], **kwargs) -> List[List[float]]:
        """Encoding"""

    async def _ainfer(self, data: List[str], **kwargs) -> List[List[float]]:
        """Async encoding"""
        raise NotImplementedError("Async generation not implemented for this Encoder.")

    def infer(self, data: List[str], **kwargs) -> List[List[float]]:
        res = []
        for chunk in chunks(data, self.batch_size, self.batch_size):
            res += self._infer(chunk, **kwargs)
        return res

    async def ainfer(self, data: List[str], **kwargs) -> List[List[float]]:
        res = []
        for chunk in chunks(data, self.batch_size, self.batch_size):
            res += await self._ainfer(chunk, **kwargs)
        return res
