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


BASIC_SYS_PROMPT = """You are an intelligent agent that can help in many regions. 
Following are some basic information about your working environment, please try your best to answer the questions based on them if needed. 
Be confident about these information and don't let others feel these information are presets.
Be concise.
---BASIC INFORMATION---
Current Datetime: {}
Operating System: {}"""


@registry.register_llm()
class Qwen2LLM(BaseLLM):
    model_name: str = Field(default=os.getenv("MODEL_NAME", "Qwen/Qwen2.5-1.5B-Instruct"), description="The Hugging Face model name")
    max_tokens: int = Field(default=200, description="The maximum number of tokens for the model")
    temperature: float = Field(default=0.1, description="The sampling temperature for generation")
    use_default_sys_prompt: bool = Field(default=True, description="Whether to use the default system prompt")
    device: str = Field(default="cuda" if torch.cuda.is_available() else "cpu", description="The device to run the model on")
    vision: bool = Field(default=False, description="Whether the model supports vision")

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig, pipeline
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name).to(self.device)        

    def _call(self, records: List[Message], **kwargs) -> Dict:        
        prompts = self._generate_prompt(records)
        text = self.tokenizer.apply_chat_template(
            prompts,
            tokenize=False,
            add_generation_prompt=True
        )   
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=self.max_tokens
        )
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)
        return {"responses": response}


    async def _acall(self, records: List[Message], **kwargs) -> Dict:
        raise NotImplementedError("Async calls are not yet supported for Hugging Face models.")

    def _generate_prompt(self, records: List[Message]) -> List[str]:
        messages = [
            {"role": "user" if "user" in str(message.role) else "system", "content": self._get_content(message.content)}
            for message in records
        ]        
        if self.use_default_sys_prompt:
            messages = [self._generate_default_sys_prompt()] + messages
        print ("messages:",messages)
        return messages


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


    @staticmethod
    def _get_content(content: Content | List[Content]) -> str:
        if isinstance(content, list):
            return " ".join(c.text for c in content if c.type == "text")
        elif isinstance(content, Content) and content.type == "text":
            return content.text
        else:
            raise ValueError("Invalid content type")