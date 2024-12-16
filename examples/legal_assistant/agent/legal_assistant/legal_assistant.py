from pathlib import Path
from typing import List, Dict

from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.utils.registry import registry
from omagent_core.models.llms.schemas import Message, Content
from omagent_core.utils.general import encode_image
from omagent_core.models.llms.prompt.parser import StrParser
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.container import container
from pydantic import Field

@registry.register_worker()
class LegalAssistant(BaseWorker, BaseLLMBackend):
    """Legal assistant with multi-turn conversation capability."""
    llm: OpenaiGPTLLM
    max_history: int = Field(default=5)  # 保存最近5轮对话

    def _run(self, user_instruction: str, *args, **kwargs):
        # 获取或初始化对话历史
        conversation_history = self.stm(self.workflow_instance_id).get('conversation_history', [])
        
        # 初始化当前对话消息列表
        chat_message = []
        
        # 系统提示词
        system_prompt = """你是一名专业的法律顾问。请基于之前的对话历史和当前问题,从法律角度提供专业的分析和建议。
        在回答时请:
        1. 引用相关法律条款
        2. 分析可能的法律风险
        3. 提供具体可行的建议
        4. 如果需要更多信息,请明确指出
        """
        chat_message.append(Message(role="system", message_type='text', content=system_prompt))
        
        # 添加历史对话记录
        for msg in conversation_history[-self.max_history:]:
            chat_message.append(Message(
                role=msg["role"],
                message_type='text',
                content=msg["content"]
            ))
            
        # 添加当前用户问题
        chat_message.append(Message(role="user", message_type='text', content=user_instruction))
        
        # 如果有图片,添加图片消息
        if self.stm(self.workflow_instance_id).get('image_cache', None):
            img = self.stm(self.workflow_instance_id)['image_cache']['<image_0>']
            chat_message.append(Message(
                role="user", 
                message_type='image', 
                content=[Content(
                    type="image_url",
                    image_url={"url": f"data:image/jpeg;base64,{encode_image(img)}"}
                )]
            ))
        
        # 获取LLM回复
        chat_complete_res = self.llm.generate(records=chat_message)
        answer = chat_complete_res["choices"][0]["message"]["content"]
        
        # 更新对话历史
        conversation_history.append({"role": "user", "content": user_instruction})
        conversation_history.append({"role": "assistant", "content": answer})
        self.stm(self.workflow_instance_id)['conversation_history'] = conversation_history
        
        # 发送回复
        self.callback.send_answer(self.workflow_instance_id, msg=answer)
        
        # 返回结果
        return {
            'answer': answer,
            'conversation_history': conversation_history
        }

    def clear_history(self):
        """清除对话历史"""
        self.stm(self.workflow_instance_id)['conversation_history'] = []
