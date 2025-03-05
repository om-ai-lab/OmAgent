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
    use_n : bool = Field(default=False)

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
        boxed_positions = [(m.start(), m.end()) for m in re.finditer(r'\\boxed{', text)]
        if not boxed_positions:
            return None

        # 查找 "Final Answer" 的位置
        final_answer_pos = text.find("Final Answer")
        
        if final_answer_pos != -1:
            # 如果找到了 "Final Answer"，选择距离它最近的 \boxed
            closest_boxed = None
            min_distance = float('inf')
            
            for start, end in boxed_positions:
                distance = abs(start - final_answer_pos)
                if distance < min_distance:
                    min_distance = distance
                    closest_boxed = (start, end)
            
            # 提取最近的 \boxed 内容
            content_start = closest_boxed[1]  # end of '\boxed{'
            content_end = find_matching_brace(text, content_start)
            
            if content_end == -1:
                return None
                
            return text[content_start:content_end-1].strip()
        else:
            # 如果没有找到 "Final Answer"，使用第一个 \boxed
            content_start = boxed_positions[0][1]  # end of '\boxed{'
            content_end = find_matching_brace(text, content_start)
            
            if content_end == -1:
                return None
                
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

        formatted_query = self.example.replace("{{query}}", query)
        #self.num = 1

        if self.use_n:
            res = self.infer(input_list=[{"query": formatted_query}], n=self.num)[0]
            all_results = [self.extract_final_answer(choice["message"]["content"]) for choice in res["choices"]]
        else:
            all_results = []  # 存储所有运行结果
            for run_idx in range(self.num):
                print(f"Running iteration {run_idx + 1}/{self.num}")
                
                # 运行单次推理
                res = self.simple_infer(query=formatted_query) # \n\nProblem: \nFind the domain of the expression $\\frac{\\sqrt{x-2}}{\\sqrt{5-x}}$.\nSolution: The expressions inside each square root must be non-negative. Therefore, $x-2 \\ge 0$, so $x\\ge2$, and $5 - x \\ge 0$, so $x \\le 5$. Also, the denominator cannot be equal to zero, so $5-x>0$, which gives $x<5$. Therefore, the domain of the expression is $\\boxed{[2,5)}$. \nFinal Answer: [2,5)\n\n\nProblem: \nIf $\\det \\mathbf{A} = 2$ and $\\det \\mathbf{B} = 12,$ then find $\\det (\\mathbf{A} \\mathbf{B}).$\nSolution: We have that $\\det (\\mathbf{A} \\mathbf{B}) = (\\det \\mathbf{A})(\\det \\mathbf{B}) = (2)(12) = \\boxed{24}.$ \nFinal Answer: 24\n\n\nProblem: \nTerrell usually lifts two 20-pound weights 12 times. If he uses two 15-pound weights instead, how many times must Terrell lift them in order to lift the same total weight?\nSolution: If Terrell lifts two 20-pound weights 12 times, he lifts a total of $2\\cdot 12\\cdot20=480$ pounds of weight. If he lifts two 15-pound weights instead for $n$ times, he will lift a total of $2\\cdot15\\cdot n=30n$ pounds of weight. Equating this to 480 pounds, we can solve for $n$:\n            \\begin{align*}\n            30n&=480\\\n            \\Rightarrow\\qquad n&=480/30=\\boxed{16}\n            \\end{align*} \nFinal Answer: 16\n\n\nProblem: \nIf the system of equations\n            \\begin{align*}\n            6x-4y&=a,\\\n            6y-9x &=b.\n            \\end{align*}\n            has a solution $(x, y)$ where $x$ and $y$ are both nonzero, find $\\frac{a}{b},$ assuming $b$ is nonzero.\nSolution: If we multiply the first equation by $-\\frac{3}{2}$, we obtain $$6y-9x=-\\frac{3}{2}a.$$Since we also know that $6y-9x=b$, we have $$-\\frac{3}{2}a=b\\Rightarrow\\frac{a}{b}=\\boxed{-\\frac{2}{3}}.$$ \nFinal Answer: -\\frac{2}{3}\nProblem: What is the least positive integer multiple of 30 that can be written with only the digits 0 and 2?\nSolution: 
                

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
                all_results.append(result['final_answer'])
                
                # 发送当前结果到回调
                self.callback.send_answer(self.workflow_instance_id, 
                                        msg=f"Run {run_idx + 1}: {result['final_answer']}")

        # 获取出现最多的答案
        most_common_answer = self.get_most_common_answer(all_results)
        body = self.llm._msg2req(self.prep_prompt([{"query": formatted_query}])[0])
        
        
        return {
            'id': id,
            'question': query,
            'body': body,
            'last_output': most_common_answer,
            'prompt_tokens': self.token_usage['prompt_tokens'],
            'completion_tokens': self.token_usage['completion_tokens']
        }

