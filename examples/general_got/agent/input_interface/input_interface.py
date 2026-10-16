from pathlib import Path
import json_repair

from omagent_core.utils.registry import registry
from omagent_core.utils.general import read_image
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.logger import logging

CURRENT_PATH = Path(__file__).parents[0]

SUPPORT_TASK= {
    'sort': "Please input number list.",
    'keyword_count': "Please input a paragraph.",
    'set_intersection': "Please input two lists of numbers."
}

@registry.register_worker()
class InputInterfaceGot(BaseWorker):

    def _run(self, *args, **kwargs):
        # # Read user input through configured input interface
        user_input_task = self.input.read_input(workflow_instance_id=self.workflow_instance_id, input_prompt=f'Welcome to use OmAgent GoT Algorithm, please input the task you want to conduct. Choices: {list(SUPPORT_TASK.keys())}. Please press enter if there is no specific task. Please be noted that the task is desgined only for got examples in the origin got paper.')
        
        task =  user_input_task['messages'][-1]['content'][0]['data']
        if task not in SUPPORT_TASK:
            task = ''

        user_input_query = self.input.read_input(workflow_instance_id=self.workflow_instance_id, input_prompt=SUPPORT_TASK[task] if task != '' else "Please input your request.")
        query = user_input_query['messages'][-1]['content'][0]['data']

        meta_input = self.input.read_input(workflow_instance_id=self.workflow_instance_id, input_prompt="Please input meta information. If there is no meta information, please press space and then enter.")
        meta = meta_input['messages'][-1]['content'][0]['data']
        if meta is not None and meta != '' and meta != ' ':
            try:    
                meta = json_repair.loads(meta)
            except Exception:
                raise ValueError("Meta information should be json. {} is not valid. Please checkout the meta information.".format(meta))
                meta = None
        else:
            meta = None
        return {'query': query, 'task': task, 'meta': meta}

