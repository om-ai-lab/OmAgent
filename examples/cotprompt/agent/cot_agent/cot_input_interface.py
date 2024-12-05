from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
from omagent_core.utils.logger import logging
from pathlib import Path

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class COTInputInterface(BaseWorker):
    """处理用户输入问题并将其存储到工作流变量中。"""
    
    def _run(self, *args, **kwargs):
        # 读取用户输入的问题
        user_input = self.input.read_input(workflow_instance_id=self.workflow_instance_id, input_prompt='请输入你的问题:')
        
        question = user_input['messages'][-1]['content'][0]['data']
        
        # 将问题存储到工作流的变量中
        self.stm(self.workflow_instance_id)['user_question'] = question
        
        return {'user_question': question}
