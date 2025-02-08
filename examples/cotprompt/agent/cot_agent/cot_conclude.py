from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.models.llms.schemas import Message, Content
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.utils.logger import logging
from pathlib import Path

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class COTConclusion(BaseLLMBackend, BaseWorker):
    """根据问题和推理步骤生成最终答案。"""
    
    llm: OpenaiGPTLLM

    def _run(self, user_question:str, reasoning_result:str, *args, **kwargs):
        # 从工作流变量中提取问题和推理结果
        # user_question = kwargs['user_question']
        # reasoning_result = kwargs['reasoning_result']
        
        # 生成最终答案的 prompt
        final_answer_prompt = self.generate_final_answer_prompt(user_question, reasoning_result)
        
        # 调用 LLM 生成最终答案
        final_answer = self.call_llm_with_prompt(final_answer_prompt)
        
        # 将最终答案存储到工作流变量中
        self.stm(self.workflow_instance_id)['final_answer'] = final_answer
        
        self.callback.send_answer(self.workflow_instance_id, msg=final_answer)
        
        return {'final_answer': final_answer}

    def generate_final_answer_prompt(self, question: str, reasoning_result: str):
        """生成最终答案的 prompt"""
        
        return f"""
        You have completed the reasoning process. Based on the following question and reasoning result, generate a concise and clear final answer.

        Question: {question}
        Reasoning steps: {reasoning_result}

        Please provide the final answer:
        """

    def call_llm_with_prompt(self, prompt: str):
        """调用 LLM 生成最终答案"""
        chat_message = []
        
        # Add text question as first message
        chat_message.append(Message(role="user", message_type='text', content=prompt))
        
        #print("chat_message++++++++++++++++++++++++++++",chat_message)
     
        response = self.llm.generate(chat_message)
        return response['choices'][0]['message']['content']
