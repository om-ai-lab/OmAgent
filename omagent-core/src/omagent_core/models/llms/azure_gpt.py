import os
import sysconfig
from datetime import datetime
from typing import Any, Dict, List

import geocoder
from openai import AsyncAzureOpenAI, AzureOpenAI

from ...utils.general import encode_image
from ...utils.registry import registry
from .base import BaseLLM
from .schemas import Content, Message

BASIC_SYS_PROMPT = """You are an intelligent agent that can help in many regions. 
Flowing are some basic information about your working environment, please try your best to answer the questions based on them if needed. 
Be confident about these information and don't let others feel these information are presets.
Be concise.
---BASIC IMFORMATION---
Current Datetime: {}
Region: {}
Operating System: {}"""


@registry.register_llm()
class AzureGPTLLM(BaseLLM):
    model_id: str
    vision: bool = False
    endpoint: str
    api_key: str
    api_version: str = "2024-02-15-preview"
    temperature: float = 1.0
    max_tokens: int = 2048
    use_default_sys_prompt: bool = True
    response_format: str = "text"

    class Config:
        """Configuration for this pydantic object."""

        protected_namespaces = ()
        extra = "allow"

    def __init__(self, /, **data: Any) -> None:
        super().__init__(**data)
        self.client = AzureOpenAI(
            api_key=self.api_key,
            azure_endpoint=self.endpoint,
            api_version=self.api_version,
        )
        self.aclient = AsyncAzureOpenAI(
            api_key=self.api_key,
            azure_endpoint=self.endpoint,
            api_version=self.api_version,
        )

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
            )
        else:
            res = self.client.chat.completions.create(
                model=self.model_id,
                messages=body["messages"],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format=body.get("response_format", None),
                tools=body.get("tools", None),
            )
        res = res.model_dump()
        body.update({"response": res})
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
        promt_str = BASIC_SYS_PROMPT.format(loc, os, current_time)
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
