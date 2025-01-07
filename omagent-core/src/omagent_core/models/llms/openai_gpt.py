import os
import sysconfig
from datetime import datetime
from typing import Any, Dict, List

import geocoder
from omagent_core.utils.container import container
from openai import AsyncOpenAI, OpenAI
from pydantic import Field

from ...utils.general import encode_image
from ...utils.registry import registry
from .base import BaseLLM
from .schemas import Content, Message

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
    stream: bool = Field(default=False, description="Whether to stream the response")
    max_tokens: int = Field(default=2048, description="The max tokens of LLM")
    use_default_sys_prompt: bool = Field(
        default=True, description="Whether to use the default system prompt"
    )
    response_format: str = Field(
        default="text", description="The response format of openai"
    )

    class Config:
        """Configuration for this pydantic object."""

        protected_namespaces = ()
        extra = "allow"

    def model_post_init(self, __context: Any) -> None:
        self.client = OpenAI(api_key=self.api_key, base_url=self.endpoint)
        # self.aclient = AsyncOpenAI(api_key=self.api_key, base_url=self.endpoint)

    def _call(self, records: List[Message], **kwargs) -> Dict:
        if self.api_key is None or self.api_key == "":
            raise ValueError("api_key is required")

        body = self._msg2req(records)
        if kwargs.get("tool_choice"):
            body["tool_choice"] = kwargs["tool_choice"]
        if kwargs.get("tools"):
            body["tools"] = kwargs["tools"]

        if self.vision:
            res = self.client.chat.completions.create(
                model=self.model_id,
                messages=body["messages"],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=self.stream,
            )
        else:
            res = self.client.chat.completions.create(
                model=self.model_id,
                messages=body["messages"],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format=body.get("response_format", None),
                tools=body.get("tools", None),
                stream=self.stream,
            )
        if self.stream:
            return res
        else:
            res = res.model_dump()
            body.update({"response": res})
            # self.callback.send_block(body)
            return res

    async def _acall(self, records: List[Message], **kwargs) -> Dict:
        if self.api_key is None or self.api_key == "":
            raise ValueError("api_key is required")

        body = self._msg2req(records)
        if kwargs.get("tool_choice"):
            body["tool_choice"] = kwargs["tool_choice"]
        if kwargs.get("tools"):
            body["tools"] = kwargs["tools"]

        if self.vision:
            res = await self.aclient.chat.completions.create(
                model=self.model_id,
                messages=body["messages"],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        else:
            res = await self.aclient.chat.completions.create(
                model=self.model_id,
                messages=body["messages"],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format=body.get("response_format", None),
                tools=body.get("tools", None),
            )
        res = res.model_dump()
        body.update({"response": res})
        # self.callback.send_block(body)
        return res

    def _msg2req(self, records: List[Message]) -> dict:
        def get_content(msg: List[Content] | Content) -> List[dict] | str:
            if isinstance(msg, list):
                return [c.model_dump(exclude_none=True) for c in msg]
            elif isinstance(msg, Content) and msg.type == "text":
                return msg.text
            else:
                raise ValueError("Invalid message type")

        messages = [
            {"role": message.role, "content": get_content(message.content)}
            for message in records
        ]
        if self.vision:
            processed_messages = []
            for message in messages:
                if message["role"] == "user":
                    if isinstance(message["content"], str):
                        message["content"] = [
                            {"type": "text", "text": message["content"]}
                        ]
            merged_dict = {}
            for message in messages:
                if message["role"] == "user":
                    merged_dict["role"] = message["role"]
                    if "content" in merged_dict:
                        merged_dict["content"] += message["content"]
                    else:
                        merged_dict["content"] = message["content"]
                else:
                    processed_messages.append(message)
            processed_messages.append(merged_dict)
            messages = processed_messages
        if self.use_default_sys_prompt:
            messages = [self._generate_default_sys_prompt()] + messages
        body = {
            "model": self.model_id,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if self.response_format != "text":
            body["response_format"] = {"type": self.response_format}
        return body

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
