from pathlib import Path

from omagent_core.utils.registry import registry
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.general import read_image

CURRENT_PATH = root_path = Path(__file__).parents[0]


@registry.register_worker()
class OutfitImageInput(BaseWorker):
    """Outfit image input processor that handles user-provided clothing images.
    
    This processor allows users to provide an image of a clothing item that they want to build
    an outfit around. It accepts either an image URL or local file path as input, reads the image,
    and caches it in the workflow's short-term memory for use by downstream processors.
    
    The processor gracefully handles cases where users choose not to provide an image or if there
    are issues reading the provided image.
    
    Attributes:
        None - This worker uses only the base worker functionality
    """

    def _run(self, *args, **kwargs):
        """Process user-provided clothing image input.
        
        Prompts the user to provide an image of a clothing item, either via URL or local path.
        Reads and caches the image if provided, handling any errors that occur during image loading.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            None - Results are stored in workflow's short-term memory
        """
        user_input = self.input.read_input(workflow_instance_id=self.workflow_instance_id, input_prompt='Please input a image of a clothing item.')
        
        content = user_input['messages'][-1]['content']
        for content_item in content:
            if content_item['type'] == 'image_url':
                image_path = content_item['data']
        
        try:
            img = read_image(input_source=image_path)
            image_cache = {'<image_0>' : img}
            self.stm(self.workflow_instance_id)['image_cache'] = image_cache
        except Exception as e:
            pass
        
        return 

