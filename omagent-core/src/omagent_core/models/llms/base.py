from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Hashable
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, TypeVar, Union

from PIL import Image
from pydantic import Field, field_validator
from tenacity import retry, stop_after_attempt, stop_after_delay

from ...base import BotBase
from ...utils.env import EnvVar
from ...utils.general import LRUCache
from ...utils.registry import registry
from .prompt.base import _OUTPUT_PARSER, StrParser
from .prompt.parser import BaseOutputParser
from .prompt.prompt import PromptTemplate
from .schemas import Message
import copy
from collections.abc import Iterator
from pprint import pprint

T = TypeVar("T", str, dict, list)


class BaseLLM(BotBase, ABC):
    cache: bool = False
    lru_cache: LRUCache = Field(default=LRUCache(EnvVar.LLM_CACHE_NUM))

    @property
    def workflow_instance_id(self) -> str:
        if hasattr(self, "_parent"):
            return self._parent.workflow_instance_id
        return None

    @workflow_instance_id.setter
    def workflow_instance_id(self, value: str):
        if hasattr(self, "_parent"):
            self._parent.workflow_instance_id = value

    @abstractmethod
    def _call(self, records: List[Message], **kwargs) -> str:
        """Run the LLM on the given prompt and input."""

    async def _acall(self, records: List[Message], **kwargs) -> str:
        """Run the LLM on the given prompt and input."""
        raise NotImplementedError("Async generation not implemented for this LLM.")

    def generate(self, records: List[Message], **kwargs) -> str: # TODO: use python native lru cache
        """Run the LLM on the given prompt and input."""
        if self.cache:
            key = self._cache_key(records)
            cached_res = self.lru_cache.get(key)
            if cached_res:
                return cached_res
            else:
                gen = self._call(records, **kwargs)
                self.lru_cache.put(key, gen)
                return gen
        else:
            return self._call(records, **kwargs)

    @retry(
        stop=(
            stop_after_delay(EnvVar.STOP_AFTER_DELAY)
            | stop_after_attempt(EnvVar.STOP_AFTER_ATTEMPT)
        ),
        reraise=True,
    )
    async def agenerate(self, records: List[str], **kwargs) -> str:
        """Run the LLM on the given prompt and input."""
        if self.cache:
            key = self._cache_key(records)
            cached_res = self.lru_cache.get(key)
            if cached_res:
                return cached_res
            else:
                gen = await self._acall(records, **kwargs)
                self.lru_cache.put(key, gen)
                return gen
        else:
            return await self._acall(records, **kwargs)

    def _cache_key(self, records: List[Message]) -> int:
        return str([item.model_dump() for item in records])

    def dict(self, *args, **kwargs):
        kwargs["exclude"] = {"lru_cache"}
        return super().model_dump(*args, **kwargs)

    def json(self, *args, **kwargs):
        kwargs["exclude"] = {"lru_cache"}
        return super().model_dump_json(*args, **kwargs)


T = TypeVar("T", str, dict, list)


class BaseLLMBackend(BotBase, ABC):
    """Prompts prepare and LLM infer"""

    output_parser: Optional[BaseOutputParser] = None
    prompts: List[PromptTemplate] = []
    llm: BaseLLM


    @property
    def token_usage(self):
        if not hasattr(self, 'workflow_instance_id'):
            raise AttributeError("workflow_instance_id not set")
        return dict(self.stm(self.workflow_instance_id).get('token_usage', defaultdict(int)))
    
    @field_validator("output_parser", mode="before")
    @classmethod
    def set_output_parser(cls, output_parser: Union[BaseOutputParser, Dict, None]):
        if output_parser is None:
            return StrParser()
        elif isinstance(output_parser, BaseOutputParser):
            return output_parser
        elif isinstance(output_parser, dict):
            return _OUTPUT_PARSER[output_parser["name"]](**output_parser)
        else:
            raise ValueError

    @field_validator("prompts", mode="before")
    @classmethod
    def set_prompts(
        cls, prompts: List[Union[PromptTemplate, Dict, str]]
    ) -> List[PromptTemplate]:
        init_prompts = []
        for prompt in prompts:
            prompt = copy.deepcopy(prompt)
            if isinstance(prompt, Path):
                if prompt.suffix == ".prompt":
                    init_prompts.append(PromptTemplate.from_file(prompt))
            elif isinstance(prompt, str):
                if prompt.endswith(".prompt"):
                    init_prompts.append(PromptTemplate.from_file(prompt))
                init_prompts.append(PromptTemplate.from_template(prompt))
            elif isinstance(prompt, dict):
                init_prompts.append(PromptTemplate.from_config(prompt))
            elif isinstance(prompt, PromptTemplate):
                init_prompts.append(prompt)
            else:
                raise ValueError(
                    "Prompt only support str, dict and PromptTemplate object"
                )
        return init_prompts

    @field_validator("llm", mode="before")
    @classmethod
    def set_llm(cls, llm: Union[BaseLLM, Dict]):
        if isinstance(llm, dict):
            return registry.get_llm(llm["name"])(**llm)
        elif isinstance(llm, BaseLLM):
            return llm
        else:
            raise ValueError("LLM only support dict and BaseLLM object")

    def prep_prompt(
        self, input_list: List[Dict[str, Any]], prompts=None, **kwargs
    ) -> List[List[Message]]:
        """Prepare prompts from inputs."""
        if prompts is None:
            prompts = self.prompts
        images = []
        if len(kwargs_images := kwargs.get("images", [])):
            images = kwargs_images
        processed_prompts = []
        for inputs in input_list:
            records = []
            for prompt in prompts:
                selected_inputs = {k: inputs.get(k, "") for k in prompt.input_variables}
                prompt_str = prompt.template                
                parts = re.split(r"(\{\{.*?\}\})", prompt_str)
                formatted_parts = []
                for part in parts:
                    if part.startswith("{{") and part.endswith("}}"):
                        part = part[2:-2].strip()
                        value = selected_inputs[part]
                        if isinstance(value, (Image.Image, list)):
                            formatted_parts.extend(
                                [value] if isinstance(value, Image.Image) else value
                            )
                        else:
                            formatted_parts.append(str(value))
                    else:
                        formatted_parts.append(str(part))
                formatted_parts = (
                    formatted_parts[0] if len(formatted_parts) == 1 else formatted_parts
                )
                if prompt.role == "system":
                    records.append(Message.system(formatted_parts))
                elif prompt.role == "user":
                    records.append(Message.user(formatted_parts))
            if len(images):
                records.append(Message.user(images))
            processed_prompts.append(records)
        return processed_prompts

    def infer(self, input_list: List[Dict[str, Any]], **kwargs) -> List[T]:
        prompts = self.prep_prompt(input_list, **kwargs)
        res = []
        stm_token_usage = self.stm(self.workflow_instance_id).get('token_usage', defaultdict(int))
        
        def process_stream(self, stream_output):

            # local deepseek
            if hasattr(next(stream_output).choices[0].delta, "reasoning_content"):
                reasoning_flag = False
                answering_flag = False
                for chunk in stream_output:
                    # output reasoning
                    if chunk.choices[0].delta.reasoning_content is not None:
                        if not reasoning_flag:
                            chunk.choices[0].delta.content = "Reasoning:" + chunk.choices[0].delta.reasoning_content
                            reasoning_flag = True
                        else:
                            chunk.choices[0].delta.content = chunk.choices[0].delta.reasoning_content
                    # output Answering
                    elif not answering_flag:
                        chunk.choices[0].delta.content = "Answer:" + chunk.choices[0].delta.content
                        answering_flag = True
                    if chunk.usage is not None:
                        for key, value in chunk.usage.dict().items():
                            if key in ["prompt_tokens", "completion_tokens", 'total_tokens']:
                                if value is not None:
                                    stm_token_usage[key] += value
                        self.stm(self.workflow_instance_id)['token_usage'] = stm_token_usage
                    yield chunk

            # ollama deepseek
            elif "deepseek" in self.llm.model_id:
                reasoning_flag = False
                answering_flag = False
                for chunk in stream_output:
                    if not reasoning_flag:
                        chunk.choices[0].delta.content = "Reasoning:" + chunk.choices[0].delta.content
                        reasoning_flag = True
                    elif not answering_flag:
                        if chunk.choices[0].delta.content == "</think>":
                            chunk.choices[0].delta.content = "Answer:"
                        answering_flag = True
                    if chunk.usage is not None:
                        for key, value in chunk.usage.dict().items():
                            if key in ["prompt_tokens", "completion_tokens", 'total_tokens']:
                                if value is not None:
                                    stm_token_usage[key] += value
                        self.stm(self.workflow_instance_id)['token_usage'] = stm_token_usage
                    yield chunk

            # models without reasoning
            else:
                for chunk in stream_output:
                    if chunk.usage is not None:
                        for key, value in chunk.usage.dict().items():
                            if key in ["prompt_tokens", "completion_tokens", 'total_tokens']:
                                if value is not None:
                                    stm_token_usage[key] += value
                        self.stm(self.workflow_instance_id)['token_usage'] = stm_token_usage
                    yield chunk
        
        for prompt in prompts:       
            output = self.llm.generate(prompt, **kwargs)
            if not isinstance(output, Iterator):
                for key, value in output.get("usage", {}).items():
                    if key in ["prompt_tokens", "completion_tokens", 'total_tokens']:
                        if value is not None:
                            stm_token_usage[key] += value
                if not self.llm.stream:
                    for choice in output["choices"]:
                        if choice.get("message"):
                            choice["message"]["content"] = self.output_parser.parse(
                                choice["message"]["content"]
                            )
                res.append(output)
            else:
                res.append(process_stream(self, output))
                
        self.stm(self.workflow_instance_id)['token_usage'] = stm_token_usage
        return res

    async def ainfer(self, input_list: List[Dict[str, Any]], **kwargs) -> List[T]:
        prompts = self.prep_prompt(input_list)
        res = []
        for prompt in prompts:
            output = await self.llm.agenerate(prompt, **kwargs)
            for key, value in output["usage"].items():
                self.token_usage[key] += value
            for choice in output["choices"]:
                if choice.get("message"):
                    choice["message"]["content"] = self.output_parser.parse(
                        choice["message"]["content"]
                    )
            res.append(output)
        return res

    def simple_infer(self, **kwargs: Any) -> T:
        return self.infer([kwargs])[0]

    async def simple_ainfer(self, **kwargs: Any) -> T:
        return await self.ainfer([kwargs])[0]