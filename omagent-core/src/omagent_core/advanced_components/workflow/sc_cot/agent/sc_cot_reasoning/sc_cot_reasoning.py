from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.schemas import Message, Content
from omagent_core.utils.logger import logging
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from omagent_core.advanced_components.workflow.sc_cot.schemas.cot_create_examples import CoTExample
from pydantic import Field
from pathlib import Path
from typing import List
import re
from collections import Counter
import random

CURRENT_PATH = Path( __file__ ).parents[ 0 ]


@registry.register_worker()
class SCCoTReasoning( BaseLLMBackend, BaseWorker ):

    prompts: List[ PromptTemplate ] = Field( default=[] )
    example: str = Field(default="")
    num : int = Field(default=5)  # 默认运行5次

    def extract_final_answer(self, text):
        """从输出文本中提取最终答案"""
        def find_matching_brace(s, start):
            """查找匹配的花括号"""
            count = 1
            i = start
            while i < len(s) and count > 0:
                if s[i] == '{':
                    count += 1
                elif s[i] == '}':
                    count -= 1
                i += 1
            return i if count == 0 else -1

        # 查找所有 \boxed{ 的位置
        boxed_starts = [m.start() for m in re.finditer(r'\\boxed{', text)]
        if not boxed_starts:
            return None

        # 获取最后一个 \boxed
        last_start = boxed_starts[-1]
        # 找到对应的结束位置
        content_start = last_start + 7  # len('\\boxed{')
        content_end = find_matching_brace(text, content_start)
        
        if content_end == -1:
            return None
            
        # 提取内容
        return text[content_start:content_end-1].strip()

    def get_most_common_answer(self, answers):
        """获取出现次数最多的答案"""
        # 过滤掉None值
        valid_answers = [ans for ans in answers if ans is not None]
        if not valid_answers:
            return None
        
        # 统计答案出现次数
        answer_counts = Counter(valid_answers)
        # 找出出现次数最多的答案
        max_count = max(answer_counts.values())
        most_common = [ans for ans, count in answer_counts.items() if count == max_count]
        
        # 如果有多个答案出现次数相同，随机选择一个
        return random.choice(most_common)

    def _run( self, id: int, query: str, *args, **kwargs ):
        """
        Executes a reasoning task based on the specified Chain-of-Thought (CoT) method.
        Args:
            id (int): The identifier for the reasoning task.
            query (str): The query string to be processed.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        Returns:
            dict: A dictionary containing the task id, question, all outputs from multiple runs.
        """

        self.prompts = [
                PromptTemplate.from_file( CURRENT_PATH.joinpath( "sc_cot.prompt" ), role="user" ),
            ]

        all_results = []  # 存储所有运行结果
        formatted_query = self.example.replace("{{query}}", query)
        
        for run_idx in range(self.num):
            print(f"Running iteration {run_idx + 1}/{self.num}")
            
            # 运行单次推理
            res = self.simple_infer(query=formatted_query)
            body = self.llm._msg2req(self.prep_prompt([{"query": formatted_query}])[0])

            # 获取完整输出
            full_output = res["choices"][0]["message"]["content"]
            
            # 提取最终答案
            final_answer = self.extract_final_answer(full_output)

            # 提取结果
            result = {
                'run_index': run_idx + 1,
                'prompt_tokens': res['usage']['prompt_tokens'],
                'completion_tokens': res['usage']['completion_tokens'],
                'last_output': full_output,
                'final_answer': final_answer
            }
            all_results.append(result)
            
            # 发送当前结果到回调
            self.callback.send_answer(self.workflow_instance_id, 
                                    msg=f"Run {run_idx + 1}: {result['final_answer']}")

        # 获取所有运行的最终答案
        all_final_answers = [result['final_answer'] for result in all_results]
        # 获取出现最多的答案
        most_common_answer = self.get_most_common_answer(all_final_answers)

        # 统计答案分布
        answer_distribution = Counter(all_final_answers)
        
        # 计算所有运行的token总数
        total_prompt_tokens = sum(result['prompt_tokens'] for result in all_results)
        total_completion_tokens = sum(result['completion_tokens'] for result in all_results)
        total_tokens = total_prompt_tokens + total_completion_tokens
        
        return {
            'id': id,
            'question': query,
            'body': body,
            'last_output': most_common_answer,
            'prompt_tokens': total_prompt_tokens,
            'completion_tokens': total_completion_tokens
        }

