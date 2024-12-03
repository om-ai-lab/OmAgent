from pathlib import Path

from omagent_core.utils.registry import registry
from omagent_core.utils.general import read_image
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.logger import logging
from omagent_core.engine.task.agent_task import TaskTree


CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class DnCInputIterface(BaseWorker):
    """
    Worker for handling user input for the Divide-and-Conquer generation task.
    """

    def _run(self, *args, **kwargs):
        user_input = self.input.read_input(workflow_instance_id=self.workflow_instance_id, input_prompt='List up the contratins')
        
        image_path = None
        # Extract text and image content from input message
        content = user_input['messages'][-1]['content']
        for content_item in content:
            if content_item['type'] == 'text':
                concepts = content_item['data']
            elif content_item['type'] == 'image_url':
                image_path = content_item['data']
        
        logging.info(f'concepts: {concepts}\nImage_path: {image_path}')
        
        # Load image from file system
        if image_path:
            img = read_image(input_source=image_path)
            
            # Store image in workflow shared memory with standard key
            image_cache = {'<image_0>' : img}
            self.stm(self.workflow_instance_id)['image_cache'] = image_cache

        return {'concepts': concepts}