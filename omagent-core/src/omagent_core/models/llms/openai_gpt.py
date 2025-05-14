import os
import sysconfig
from datetime import datetime
from typing import Any, Dict, List, Union, Optional

import geocoder
from openai import AsyncOpenAI, OpenAI
from openai._types import NOT_GIVEN, NotGiven

from pydantic import Field

from omagent_core.utils.registry import registry
from omagent_core.models.llms.base import BaseLLM
from omagent_core.models.llms.schemas import Content, Message

BASIC_SYS_PROMPT = """You are an intelligent agent that can help in many regions. 
Flowing are some basic information about your working environment, please try your best to answer the questions based on them if needed. 
Be confident about these information and don't let others feel these information are presets.
Be concise.
---BASIC INFORMATION---
Current Datetime: {}
Region: {}
Operating System: {}"""


@registry.register_llm()
class OpenaiGPTLLM(BaseLLM):
    model_id: str = Field(
        default=os.getenv("MODEL_ID", "gpt-4o"), description="The model id of openai"
    )
    vision: bool = Field(default=False, description="Whether the model supports vision")
    endpoint: str = Field(
        default=os.getenv("ENDPOINT", "https://api.openai.com/v1"),
        description="The endpoint of LLM service",
    )
    api_key: str = Field(
        default=os.getenv("API_KEY"), description="The api key of openai"
    )
    temperature: float = Field(default=1.0, description="The temperature of LLM")
    top_p: float = Field(
        default=1.0,
        description="The top p of LLM, controls diversity of responses. Should not be used together with temperature - use either temperature or top_p but not both",
    )
    stream: bool = Field(default=False, description="Whether to stream the response")
    max_tokens: int = Field(default=2048, description="The max tokens of LLM")
    use_default_sys_prompt: bool = Field(
        default=True, description="Whether to use the default system prompt"
    )
    response_format: Optional[Union[dict, str]] = Field(default='text', description="The response format of openai")
    n: int = Field(default=1, description="The number of responses to generate")
    frequency_penalty: float = Field(
        default=0, description="The frequency penalty of LLM, -2 to 2"
    )
    logit_bias: Optional[dict] = Field(
        default=None, description="The logit bias of LLM"
    )
    logprobs: bool = Field(default=False, description="The logprobs of LLM")
    top_logprobs: Optional[int] = Field(
        default=None,
        description="The top logprobs of LLM, logprobs must be set to true if this parameter is used",
    )
    stop: Union[str, List[str], NotGiven] = Field(
        default=NOT_GIVEN,
        description="Specifies stop sequences that will halt text generation, can be string or list of strings",
    )
    stream_options: Optional[dict] = Field(
        default=None,
        description="Configuration options for streaming responses when stream=True",
    )
    tools: Optional[List[dict]] = Field(
        default=None,
        description="A list of function tools (max 128) that the model can call, each requiring a type, name and optional description/parameters defined in JSON Schema format.",
    )
    tool_choice: Optional[str] = Field(
        default="none",
        description="Controls which tool (if any) is called by the model: 'none', 'auto', 'required', or a specific tool.",
    )

    class Config:
        """Configuration for this pydantic object."""

        protected_namespaces = ()
        extra = "allow"

    def check_response_format(self) -> Optional[dict]:
        if isinstance(self.response_format, str):
            if self.response_format == "text":
                self.response_format = {"type": "text"}
            elif self.response_format == "json_object":
                self.response_format = {"type": "json_object"}
        elif isinstance(self.response_format, dict):
            for key, value in self.response_format.items():
                if key not in ["type", "json_schema"]:
                    raise ValueError(f"Invalid response format key: {key}")
                if key == "type":
                    if value not in ["text", "json_object"]:
                        raise ValueError(f"Invalid response format value: {value}")
                elif key == "json_schema":
                    if not isinstance(value, dict):
                        raise ValueError(f"Invalid response format value: {value}")
        else:
            raise ValueError(f"Invalid response format: {self.response_format}")

    def model_post_init(self, __context: Any) -> None:
        self.check_response_format()
        self.client = OpenAI(api_key=self.api_key, base_url=self.endpoint)
        self.aclient = AsyncOpenAI(api_key=self.api_key, base_url=self.endpoint)

    def _call(self, records: List[Message], **kwargs) -> Dict:
        if self.api_key is None or self.api_key == "":
            raise ValueError("api_key is required")

        if self.vision:
            res = self.client.chat.completions.create(
                model=self.model_id,
                messages=records,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                stream=kwargs.get("stream", self.stream),
                n=kwargs.get("n", self.n),
                top_p=kwargs.get("top_p", self.top_p),
                frequency_penalty=kwargs.get(
                    "frequency_penalty", self.frequency_penalty
                ),
                logit_bias=kwargs.get("logit_bias", self.logit_bias),
                logprobs=kwargs.get("logprobs", self.logprobs),
                top_logprobs=kwargs.get("top_logprobs", self.top_logprobs),
                stop=kwargs.get("stop", self.stop),
                stream_options=kwargs.get("stream_options", self.stream_options),
            )
        else:
            res = self.client.chat.completions.create(
                model=self.model_id,
                messages=records,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                response_format=kwargs.get("response_format", self.response_format),
                tools=kwargs.get("tools", None),
                tool_choice=kwargs.get("tool_choice", "none"),
                stream=kwargs.get("stream", self.stream),
                n=kwargs.get("n", self.n),
                top_p=kwargs.get("top_p", self.top_p),
                frequency_penalty=kwargs.get(
                    "frequency_penalty", self.frequency_penalty
                ),
                logit_bias=kwargs.get("logit_bias", self.logit_bias),
                logprobs=kwargs.get("logprobs", self.logprobs),
                top_logprobs=kwargs.get("top_logprobs", self.top_logprobs),
                stop=kwargs.get("stop", self.stop),
                stream_options=kwargs.get("stream_options", self.stream_options),
            )

        if kwargs.get("stream", self.stream):
            return res
        else:
            return res.model_dump()

    async def _acall(self, records: List[Message], **kwargs) -> Dict:
        if self.api_key is None or self.api_key == "":
            raise ValueError("api_key is required")

        if self.vision:
            res = await self.aclient.chat.completions.create(
                model=self.model_id,
                messages=records,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                n=kwargs.get("n", self.n),
                top_p=kwargs.get("top_p", self.top_p),
                frequency_penalty=kwargs.get(
                    "frequency_penalty", self.frequency_penalty
                ),
                logit_bias=kwargs.get("logit_bias", self.logit_bias),
                logprobs=kwargs.get("logprobs", self.logprobs),
                top_logprobs=kwargs.get("top_logprobs", self.top_logprobs),
                stop=kwargs.get("stop", self.stop),
                stream_options=kwargs.get("stream_options", self.stream_options),
            )
        else:
            res = await self.aclient.chat.completions.create(
                model=self.model_id,
                messages=records,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                response_format=kwargs.get("response_format", self.response_format),
                tools=kwargs.get("tools", None),
                n=kwargs.get("n", self.n),
                top_p=kwargs.get("top_p", self.top_p),
                frequency_penalty=kwargs.get(
                    "frequency_penalty", self.frequency_penalty
                ),
                logit_bias=kwargs.get("logit_bias", self.logit_bias),
                logprobs=kwargs.get("logprobs", self.logprobs),
                top_logprobs=kwargs.get("top_logprobs", self.top_logprobs),
                stop=kwargs.get("stop", self.stop),
                stream_options=kwargs.get("stream_options", self.stream_options),
            )
        return res.model_dump()

    def _generate_default_sys_prompt(self) -> Dict:
        loc = self._get_location()
        os = self._get_linux_distribution()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        promt_str = BASIC_SYS_PROMPT.format(current_time, loc, os)
        return {"role": "system", "content": promt_str}

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