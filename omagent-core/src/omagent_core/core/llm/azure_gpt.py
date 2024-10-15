import os
import sysconfig
from datetime import datetime
from typing import Any, Dict, List

import geocoder
from openai import AsyncAzureOpenAI, AzureOpenAI

from ...schemas.dev import Content, Message
from ...utils.general import encode_image
from ...utils.registry import registry
from .base import BaseLLM

# Define a basic system prompt template
BASIC_SYS_PROMPT = """You are an intelligent agent that can help in many regions.
Following are some basic information about your working environment, please try your best to answer the questions based on them if needed.
Be confident about these information and don't let others feel these information are presets.
Be concise.
---BASIC INFORMATION---
Current Datetime: {}
Region: {}
Operating System: {}"""

@registry.register_llm()
class AzureGPTLLM(BaseLLM):
    """
    AzureGPTLLM is a class that interfaces with Azure's OpenAI service to generate responses based on input messages.
    """

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
        """
        Initialize the AzureGPTLLM with the provided data.
        """
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
        """
        Synchronously call the Azure OpenAI service with the provided messages.
        """
        if not self.api_key:
            raise ValueError("api_key is required")

        # Handle image caching
        self._handle_image_cache(records, kwargs)

        # Prepare the request body
        body = self._msg2req(records, kwargs)

        # Make the API call
        res = self._make_api_call(body)
        res = res.model_dump()
        body.update({"response": res})
        self.callback.send_block(body)
        return res

    async def _acall(self, records: List[Message], **kwargs) -> Dict:
        """
        Asynchronously call the Azure OpenAI service with the provided messages.
        """
        if not self.api_key:
            raise ValueError("api_key is required")

        # Handle image caching
        self._handle_image_cache(records, kwargs)

        # Prepare the request body
        body = self._msg2req(records, kwargs)

        # Make the API call
        res = await self._make_async_api_call(body)
        res = res.model_dump()
        body.update({"response": res})
        self.callback.send_block(body)
        return res

    def _handle_image_cache(self, records: List[Message], kwargs: Dict) -> None:
        """
        Handle image caching for the messages.
        """
        if len(self.stm.image_cache):
            for record in records:
                record.combine_image_message(
                    image_cache={
                        key: encode_image(value)
                        for key, value in self.stm.image_cache.items()
                    }
                )
        elif len(kwargs.get("images", [])):
            image_cache = {f"<image_{index}>": each for index, each in enumerate(kwargs["images"])}
            for record in records:
                record.combine_image_message(
                    image_cache={
                        key: encode_image(value) for key, value in image_cache.items()
                    }
                )

    def _msg2req(self, records: List[Message], kwargs: Dict) -> dict:
        """
        Convert messages to a request format suitable for the API.
        """
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

        # Process messages for vision mode
        if self.vision:
            messages = self._process_vision_messages(messages)

        # Add default system prompt if required
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

        # Add tools and tool choices if provided
        if kwargs.get("tool_choice"):
            body["tool_choice"] = kwargs["tool_choice"]
        if kwargs.get("tools"):
            body["tools"] = kwargs["tools"]

        return body

    def _process_vision_messages(self, messages: List[Dict]) -> List[Dict]:
        """
        Process messages for vision mode.
        """
        processed_messages = []
        merged_dict = {}
        for message in messages:
            if message["role"] == "user":
                if isinstance(message["content"], str):
                    message["content"] = [{"type": "text", "text": message["content"]}]
                if "content" in merged_dict:
                    merged_dict["content"] += message["content"]
                else:
                    merged_dict["content"] = message["content"]
            else:
                processed_messages.append(message)
        processed_messages.append(merged_dict)
        return processed_messages

    def _generate_default_sys_prompt(self) -> Dict:
        """
        Generate the default system prompt with current environment details.
        """
        loc = self._get_location()
        os = self._get_linux_distribution()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt_str = BASIC_SYS_PROMPT.format(current_time, loc, os)
        return {"role": "system", "content": prompt_str}

    def _get_linux_distribution(self) -> str:
        """
        Get the Linux distribution name.
        """
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
        """
        Get the current location based on IP address.
        """
        g = geocoder.ip("me")
        if g.ok:
            return f"{g.city}, {g.country}"
        else:
            return "unknown"

    def _make_api_call(self, body: Dict) -> Any:
        """
        Make a synchronous API call to Azure OpenAI.
        """
        if self.vision:
            return self.client.chat.completions.create(
                model=self.model_id,
                messages=body["messages"],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        else:
            return self.client.chat.completions.create(
                model=self.model_id,
                messages=body["messages"],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format=body.get("response_format", None),
                tools=body.get("tools", None),
            )

    async def _make_async_api_call(self, body: Dict) -> Any:
        """
        Make an asynchronous API call to Azure OpenAI.
        """
        if self.vision:
            return await self.aclient.chat.completions.create(
                model=self.model_id,
                messages=body["messages"],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        else:
            return await self.aclient.chat.completions.create(
                model=self.model_id,
                messages=body["messages"],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format=body.get("response_format", None),
                tools=body.get("tools", None),
            )
