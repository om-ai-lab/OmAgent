import os
from datetime import datetime
from typing import Any, Dict, List

from pydantic import Field
from .schemas import Content, Message
from ...utils.registry import registry
from .base import BaseLLM
import torch
import sysconfig
import geocoder
from qwen_vl_utils import process_vision_info

BASIC_SYS_PROMPT = """You are an intelligent agent that can help in many regions. 
Following are some basic information about your working environment, please try your best to answer the questions based on them if needed. 
Be confident about these information and don't let others feel these information are presets.
Be concise.
---BASIC INFORMATION---
Current Datetime: {}
Operating System: {}"""


@registry.register_llm()
class Qwen2_VL(BaseLLM):
    model_name: str = Field(default=os.getenv("MODEL_NAME", "Qwen/Qwen2-VL-2B-Instruct"), description="The Hugging Face model name")
    max_tokens: int = Field(default=128, description="The maximum number of tokens for the model")
    temperature: float = Field(default=0.1, description="The sampling temperature for generation")
    use_default_sys_prompt: bool = Field(default=False, description="Whether to use the default system prompt")
    device: str = Field(default="cuda" if torch.cuda.is_available() else "cpu", description="The device to run the model on")

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        from transformers import AutoTokenizer, AutoProcessor, Qwen2VLForConditionalGeneration
        self.processor = AutoProcessor.from_pretrained(self.model_name,min_pixels=256 * 28 * 28, max_pixels=512 * 28 * 28)
        self.model = Qwen2VLForConditionalGeneration.from_pretrained(self.model_name, torch_dtype="auto", device_map="auto").to(self.device)
        

    def _call(self, records: List[Message], **kwargs) -> Dict:
        prompts, image_inputs, video_inputs = self._prepare_inputs(records)
        inputs = self.processor(
            text=[prompts],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        ).to(self.device)
        
        inputs.input_ids = inputs.input_ids.to(self.device)

        generated_ids = self.model.generate(
            **inputs,
            max_new_tokens=self.max_tokens
        )
        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids.to(self.device), generated_ids)
        ]
        response = self.processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )
        return {"responses": response}

    async def _acall(self, records: List[Message], **kwargs) -> Dict:
        raise NotImplementedError("Async calls are not yet supported for Hugging Face models.")
    
    def convert_messages(self, messages):
        for message in messages:
            for content in message.get("content", []):
                if content.get("type") == "image" and "data" in content:
                    content["image"] = content.pop("data")
                if content.get("type") == "text" and "data" in content:
                    content["text"] = content.pop("data")
        return messages

    def _prepare_inputs(self, records: List[Message]):
        records = records["messages"]
        records = self.convert_messages(records) 
        prompts = self._generate_prompt(records)
        image_inputs, video_inputs = process_vision_info(records)
        return prompts, image_inputs, video_inputs

    def _generate_prompt(self, records: List[Message]) -> str:                
        messages = records
        #if self.use_default_sys_prompt:
        #    messages = [self._generate_default_sys_prompt()] + messages
        return self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        

    def _generate_default_sys_prompt(self) -> Dict:
        loc = self._get_location()
        os = self._get_linux_distribution()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt_str = BASIC_SYS_PROMPT.format(current_time, os)
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

    @staticmethod
    def _get_content(content: Content | List[Content]) -> str:
        if isinstance(content, list):
            return " ".join(c.text for c in content if c.type == "text")
        elif isinstance(content, Content) and content.type == "text":
            return content.text
        else:
            raise ValueError("Invalid content type")
