from pathlib import Path
from typing import List

from omagent_core.core.llm.base import BaseLLMBackend
from omagent_core.core.node.base import BaseProcessor
from omagent_core.core.node.dnc.interface import DnCInterface
from omagent_core.core.prompt.prompt import PromptTemplate
from omagent_core.handlers.data_handler.ltm import LTM
from omagent_core.utils.registry import registry
from pydantic import Field

CURRENT_PATH = root_path = Path(__file__).parents[0]


@registry.register_node()
class Conclude(BaseLLMBackend, BaseProcessor):
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("sys_prompt.prompt"), role="system"
            ),
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("user_prompt.prompt"), role="user"
            ),
        ]
    )

    def _run(self, args: DnCInterface, ltm: LTM) -> DnCInterface:
        chat_complete_res = self.simple_infer(
            task=args.task.find_root_task().task,
            result=args.last_output,
            img_placeholders="".join(list(self.stm.image_cache.keys())),
        )
        self.callback.send_block(
            f'Answer: {chat_complete_res["choices"][0]["message"]["content"]}'
        )
        args.last_output = chat_complete_res["choices"][0]["message"]["content"]
        args.stm = self.token_usage.items()
        for key, value in self.token_usage.items():
            print(f"Usage of {key}: {value}")
        return args

    async def _arun(self, args: DnCInterface, ltm: LTM) -> DnCInterface:
        chat_complete_res = await self.simple_ainfer(
            task=args.task.find_root_task().task,
            result=args.last_output,
            img_placeholders="".join(list(self.stm.image_cache.keys())),
        )
        self.callback.send_block(
            f'Answer: {chat_complete_res["choices"][0]["message"]["content"]}'
        )
        args.last_output = chat_complete_res["choices"][0]["message"]["content"]
        args.stm = self.token_usage.items()
        for key, value in self.token_usage.items():
            print(f"Usage of {key}: {value}")
        return args
