import os
import re
import sysconfig
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import geocoder
from openai import AsyncOpenAI, OpenAI
from pydantic import Field

from omagent_core.models.llms.base import BaseLLM
from omagent_core.models.llms.schemas import Content, Message
from omagent_core.utils.registry import registry

BASIC_SYS_PROMPT = """You are an intelligent agent that can help in many regions.
Flowing are some basic information about your working environment, please try your best to answer the questions based on them if needed.
Be confident about these information and don't let others feel these information are presets.
Be concise.
---BASIC INFORMATION---
Current Datetime: {}
Region: {}
Operating System: {}"""

# MiniMax supported models and their context window sizes
MINIMAX_MODELS = {
    "MiniMax-M3": 1000000,          # 1M context
    "MiniMax-M2.7": 1048576,        # 1M context
    "MiniMax-M2.7-highspeed": 1048576,  # 1M context
    "MiniMax-M2.5": 204800,         # 204K context
    "MiniMax-M2.5-highspeed": 204800,   # 204K context
}

MINIMAX_API_BASE = "https://api.minimax.io/v1"


@registry.register_llm()
class MiniMaxLLM(BaseLLM):
    """MiniMax LLM provider using OpenAI-compatible API.

    MiniMax provides large language models accessible via an OpenAI-compatible
    API endpoint. Supported models include MiniMax-M3, MiniMax-M2.7,
    MiniMax-M2.7-highspeed, MiniMax-M2.5, and MiniMax-M2.5-highspeed.

    Configuration example (YAML):
        name: MiniMaxLLM
        model_id: MiniMax-M3
        api_key: ${env| MINIMAX_API_KEY}
        temperature: 0
    """

    model_id: str = Field(
        default=os.getenv("MINIMAX_MODEL_ID", "MiniMax-M3"),
        description="The model id of MiniMax LLM",
    )
    api_key: str = Field(
        default=os.getenv("MINIMAX_API_KEY"),
        description="The api key of MiniMax",
    )
    endpoint: str = Field(
        default=os.getenv("MINIMAX_ENDPOINT", MINIMAX_API_BASE),
        description="The endpoint of MiniMax LLM service",
    )
    temperature: float = Field(
        default=0.7,
        description="The temperature of LLM, must be in [0, 1.0]",
    )
    top_p: float = Field(
        default=1.0,
        description="The top p of LLM",
    )
    stream: bool = Field(default=False, description="Whether to stream the response")
    max_tokens: int = Field(default=2048, description="The max tokens of LLM")
    use_default_sys_prompt: bool = Field(
        default=True, description="Whether to use the default system prompt"
    )
    response_format: Optional[Union[dict, str]] = Field(
        default="text", description="The response format"
    )
    n: int = Field(default=1, description="The number of responses to generate")
    stop: Union[str, List[str], None] = Field(
        default=None, description="Specifies stop sequences"
    )
    stream_options: Optional[dict] = Field(
        default=None, description="Configuration options for streaming responses"
    )
    tools: Optional[List[dict]] = Field(
        default=None, description="A list of function tools the model can call"
    )
    tool_choice: Optional[str] = Field(
        default="none",
        description="Controls which tool is called by the model",
    )

    class Config:
        """Configuration for this pydantic object."""

        protected_namespaces = ()
        extra = "allow"

    def _clamp_temperature(self, temperature: float) -> float:
        """Clamp temperature to MiniMax's accepted range [0, 1.0]."""
        return max(0.0, min(1.0, temperature))

    def check_response_format(self) -> None:
        if isinstance(self.response_format, str):
            if self.response_format == "text":
                self.response_format = {"type": "text"}
            elif self.response_format == "json_object":
                self.response_format = {"type": "json_object"}
        elif isinstance(self.response_format, dict):
            for key, value in self.response_format.items():
                if key not in ["type"]:
                    raise ValueError(f"Invalid response format key: {key}")
                if key == "type":
                    if value not in ["text", "json_object"]:
                        raise ValueError(f"Invalid response format value: {value}")
        else:
            raise ValueError(f"Invalid response format: {self.response_format}")

    def model_post_init(self, __context: Any) -> None:
        self.temperature = self._clamp_temperature(self.temperature)
        self.check_response_format()
        self.client = OpenAI(api_key=self.api_key, base_url=self.endpoint)
        self.aclient = AsyncOpenAI(api_key=self.api_key, base_url=self.endpoint)

    def _strip_think_tags(self, content: str) -> str:
        """Strip <think>...</think> tags from model response.

        If stripping would result in empty content, returns the original
        content with only the tags removed (preserving inner text).
        """
        if content is None:
            return content
        stripped = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        if stripped:
            return stripped
        # If all content was inside think tags, remove tags but keep inner text
        fallback = re.sub(r"</?think>", "", content).strip()
        return fallback if fallback else content

    def _call(self, records: List[Message], **kwargs) -> Dict:
        if self.api_key is None or self.api_key == "":
            raise ValueError("api_key is required")

        messages = self._msg2req(records)
        temperature = self._clamp_temperature(
            kwargs.get("temperature", self.temperature)
        )

        res = self.client.chat.completions.create(
            model=self.model_id,
            messages=messages,
            temperature=temperature,
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            response_format=kwargs.get("response_format", self.response_format),
            tools=kwargs.get("tools", None),
            tool_choice=kwargs.get("tool_choice", None),
            stream=kwargs.get("stream", self.stream),
            n=kwargs.get("n", self.n),
            top_p=kwargs.get("top_p", self.top_p),
            stop=kwargs.get("stop", self.stop),
            stream_options=kwargs.get("stream_options", self.stream_options),
        )

        if kwargs.get("stream", self.stream):
            return res
        else:
            result = res.model_dump()
            # Strip think tags from response content
            for choice in result.get("choices", []):
                msg = choice.get("message", {})
                if msg.get("content"):
                    msg["content"] = self._strip_think_tags(msg["content"])
            return result

    async def _acall(self, records: List[Message], **kwargs) -> Dict:
        if self.api_key is None or self.api_key == "":
            raise ValueError("api_key is required")

        messages = self._msg2req(records)
        temperature = self._clamp_temperature(
            kwargs.get("temperature", self.temperature)
        )

        res = await self.aclient.chat.completions.create(
            model=self.model_id,
            messages=messages,
            temperature=temperature,
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            response_format=kwargs.get("response_format", self.response_format),
            tools=kwargs.get("tools", None),
            n=kwargs.get("n", self.n),
            top_p=kwargs.get("top_p", self.top_p),
            stop=kwargs.get("stop", self.stop),
            stream_options=kwargs.get("stream_options", self.stream_options),
        )

        result = res.model_dump()
        # Strip think tags from response content
        for choice in result.get("choices", []):
            msg = choice.get("message", {})
            if msg.get("content"):
                msg["content"] = self._strip_think_tags(msg["content"])
        return result

    def _msg2req(self, records: List[Message]) -> list:
        def get_content(msg: List[Content] | Content) -> List[dict] | str:
            if isinstance(msg, list):
                return [c.model_dump(exclude_none=True) for c in msg]
            elif isinstance(msg, Content) and msg.type == "text":
                return msg.text
            elif isinstance(msg, Content) and msg.type == "image_url":
                return [msg.model_dump(exclude_none=True)]
            else:
                raise ValueError("Invalid message type")

        messages = [
            {"role": message.role, "content": get_content(message.content)}
            for message in records
        ]
        if self.use_default_sys_prompt:
            messages = [self._generate_default_sys_prompt()] + messages
        return messages

    def _generate_default_sys_prompt(self) -> Dict:
        loc = self._get_location()
        os_info = self._get_linux_distribution()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt_str = BASIC_SYS_PROMPT.format(current_time, loc, os_info)
        return {"role": "system", "content": prompt_str}

    def _get_linux_distribution(self) -> str:
        platform = sysconfig.get_platform()
        if "linux" in platform:
            if os.path.exists("/etc/lsb-release"):
                with open("/etc/lsb-release", "r") as f:
                    for line in f:
                        if line.startswith("DISTRIB_DESCRIPTION="):
                            return line.split("=")[1].strip()
            elif os.path.exists("/etc/os-release"):
                with open("/etc/os-release", "r") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            return line.split("=")[1].strip()
        return platform

    def _get_location(self) -> str:
        g = geocoder.ip("me")
        if g.ok:
            return g.city + "," + g.country
        else:
            return "unknown"
