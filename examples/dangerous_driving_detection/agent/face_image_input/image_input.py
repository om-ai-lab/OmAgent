from pathlib import Path

from omagent_core.utils.registry import registry
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.general import read_image

CURRENT_PATH = root_path = Path(__file__).parents[0]


@registry.register_worker()
class FaceImageInput(BaseWorker):

    def _run(self, *args, **kwargs):
        
        user_input = self.input.read_input(workflow_instance_id=self.workflow_instance_id, input_prompt="Please enter the face image while driving")

        content = user_input['messages'][-1]['content']
        for content_item in content:
            if content_item['type'] == 'image_url':
                image_path = content_item['data']
        
        try:
            img = read_image(input_source=image_path)
            image_cache = {'<image_0>' : img}
            self.stm(self.workflow_instance_id)['face_image_cache'] = image_cache
        except Exception as e:
            pass
        
        return 

