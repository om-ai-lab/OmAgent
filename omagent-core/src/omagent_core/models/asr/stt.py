import io
from typing import Any, Optional

from openai import NOT_GIVEN, AsyncOpenAI, OpenAI
from pydub import AudioSegment

from ...base import BotBase


class STT(BotBase):
    model_id: str = "whisper-1"
    endpoint: Optional[str] = None
    api_key: str
    language: Optional[str] = None
    response_format: str = "verbose_json"

    class Config:
        """Configuration for this pydantic object."""

        extra = "allow"
        protected_namespaces = ()

    def __init__(self, /, **data: Any) -> None:
        super().__init__(**data)
        self.client = OpenAI(base_url=self.endpoint, api_key=self.api_key)
        self.aclient = AsyncOpenAI(base_url=self.endpoint, api_key=self.api_key)

    def _as2bytes(self, audio: AudioSegment) -> io.BytesIO:
        audio_bytes = io.BytesIO()
        audio.export(audio_bytes, format="mp3")
        audio_bytes.seek(0)
        audio_bytes.name = "buffer.mp3"
        return audio_bytes

    def infer(self, audio: AudioSegment) -> dict:
        audio_bytes = self._as2bytes(audio)

        trans = self.client.audio.transcriptions.create(
            model=self.model_id,
            file=audio_bytes,
            response_format=self.response_format,
            language=NOT_GIVEN if self.language is None else self.language,
        )
        return trans.to_dict()

    async def ainfer(self, audio: AudioSegment) -> dict:
        audio_bytes = self._as2bytes(audio)

        trans = await self.aclient.audio.transcriptions.create(
            model=self.model_id,
            file=audio_bytes,
            response_format=self.response_format,
            language=NOT_GIVEN if self.language is None else self.language,
        )
        return trans.to_dict()
