from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.schemas import Message, Content
from omagent_core.utils.logger import logging
from pathlib import Path

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class COTReasoning(BaseLLMBackend, BaseWorker):
    """根据问题生成推理过程的中间数据，不给出答案。"""
    
    llm: OpenaiGPTLLM

    def _run(self, user_question:str,*args, **kwargs):
        # 从工作流变量中提取问题
        #user_question = kwargs['user_question']
        
        # 生成推理过程的 prompt
        reasoning_prompt = self.generate_reasoning_prompt(user_question)
        #print("reasoning_prompt++++++++++++++++++++++++++++",reasoning_prompt)
        
        # 调用 LLM 生成推理步骤
        reasoning_result = self.call_llm_with_prompt(reasoning_prompt)
        
        # 将推理结果存储到工作流变量中
        self.stm(self.workflow_instance_id)['reasoning_result'] = reasoning_result
        
        self.callback.send_answer(self.workflow_instance_id, msg=reasoning_result)
        
        return {'reasoning_result': reasoning_result}

    def generate_reasoning_prompt(self, question: str):
        """生成推理过程的 prompt"""
        return f"""
        Please reason step by step based on the following question and provide the reasoning process:

        question: {question}

        Reasoning Steps:
        1. Analyze the question and consider possible solutions.
        2. Reason through the different aspects of the question step by step.
        3. Only provide the reasoning process, do not give the final answer.
        
        Please begin reasoning:
        """

    def call_llm_with_prompt(self, prompt: str):
        """调用 LLM 生成推理步骤"""
    
        
        chat_message = []
        
        # Add text question as first message
        chat_message.append(Message(role="user", message_type='text', content=prompt))
        
        #print("chat_message++++++++++++++++++++++++++++",chat_message)
     
        response = self.llm.generate(chat_message)
        if response is None:
            raise ValueError("LLM inference returned None.")
        return response['choices'][0]['message']['content']
