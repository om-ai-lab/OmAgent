from typing import Any, List

from openai import AsyncOpenAI, OpenAI

from ...utils.registry import registry
from .base import EncoderBase


@registry.register_encoder()
class OpenaiTextEmbeddingV3(EncoderBase):
    model_id: str = "text-embedding-3-large"
    api_key: str
    dim: int = 3072

    class Config:
        """Configuration for this pydantic object."""

        protected_namespaces = ()
        extra = "allow"

    def __init__(self, /, **data: Any) -> None:
        super().__init__(**data)
        self.client = OpenAI(base_url=self.endpoint, api_key=self.api_key)
        self.aclient = AsyncOpenAI(base_url=self.endpoint, api_key=self.api_key)

    def _infer(self, data: List[str], **kwargs) -> List[List[float]]:
        res = self.client.embeddings.create(input=data, model=self.model_id)
        return [item.embedding for item in res.data]

    async def _ainfer(self, data: List[str], **kwargs) -> List[List[float]]:
        res = await self.aclient.embeddings.create(input=data, model=self.model_id)
        return [item.embedding for item in res.data]
