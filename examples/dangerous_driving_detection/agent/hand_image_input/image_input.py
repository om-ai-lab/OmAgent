from pathlib import Path

from omagent_core.utils.registry import registry
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.general import read_image

CURRENT_PATH = root_path = Path(__file__).parents[0]


@registry.register_worker()
class HandImageInput(BaseWorker):
    """Hand image input processor.
    
    It accepts either an image URL or local file path as input, reads the image,
    and caches it in the workflow's short-term memory for use by downstream processors.
    
    The processor gracefully handles cases where users choose not to provide an image or if there
    are issues reading the provided image.
    
    Attributes:
        None - This worker uses only the base worker functionality
    """

    def _run(self, *args, **kwargs):
        
        user_input = self.input.read_input(workflow_instance_id=self.workflow_instance_id, input_prompt="Please enter the hand image while driving")
        
        content = user_input['messages'][-1]['content']
        for content_item in content:
            if content_item['type'] == 'image_url':
                image_path = content_item['data']
        
        try:
            img = read_image(input_source=image_path)
            image_cache = {'<image_0>' : img}
            self.stm(self.workflow_instance_id)['hand_image_cache'] = image_cache
        except Exception as e:
            pass
        
        return 

