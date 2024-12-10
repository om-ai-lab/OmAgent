from pathlib import Path

from omagent_core.utils.registry import registry
from omagent_core.utils.general import read_image
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.logger import logging

CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class InputInterface(BaseWorker):
    """Enhanced input interface with conversation control."""

    def _run(self, *args, **kwargs):
        # 读取用户输入
        user_input = self.input.read_input(
            workflow_instance_id=self.workflow_instance_id, 
            input_prompt='请输入您的法律问题(输入"清除历史"可以开始新的对话):'
        )
        
        image_path = None
        content = user_input['messages'][-1]['content']
        
        # 提取文本和图片内容
        for content_item in content:
            if content_item['type'] == 'text':
                user_instruction = content_item['data']
            elif content_item['type'] == 'image_url':
                image_path = content_item['data']
        
        # 处理特殊命令
        if user_instruction.strip() == "清除历史":
            self.stm(self.workflow_instance_id)['conversation_history'] = []
            return {'user_instruction': '对话历史已清除,请输入新的问题。'}
            
        logging.info(f'User_instruction: {user_instruction}\nImage_path: {image_path}')
        
        # 处理图片
        if image_path:
            img = read_image(input_source=image_path)
            image_cache = {'<image_0>' : img}
            self.stm(self.workflow_instance_id)['image_cache'] = image_cache

        return {'user_instruction': user_instruction}
