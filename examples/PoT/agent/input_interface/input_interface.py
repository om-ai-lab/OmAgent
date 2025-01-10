from pathlib import Path

from omagent_core.utils.registry import registry
from omagent_core.utils.general import read_image
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.logger import logging


CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class PoTInputInterface(BaseWorker):
    """Input interface processor that handles user questions and example inputs.
    
    This processor manages the interactive input collection process for math problem solving:
    1. Collects a math word problem from the user
    2. Optionally collects example problems/solutions for few-shot learning
    3. Optionally collects multiple choice options if applicable
    4. Validates and formats all inputs appropriately
    5. Returns a structured dictionary containing the processed inputs
    
    The interface is designed to be flexible, allowing both basic question-only
    inputs as well as more complex scenarios with examples and multiple choice options.
    """

    def _run(self, *args, **kwargs):
        # Prompt user for the main math question and extract text content
        input = self.input.read_input(workflow_instance_id=self.workflow_instance_id, input_prompt='Please input a math related question:')
        content = input['messages'][-1]['content']
        for content_item in content:
            if content_item['type'] == 'text':
                query = content_item['data']
        
        # Collect optional example problems/solutions for few-shot learning
        # User can input "None" to skip this step
        input = self.input.read_input(workflow_instance_id=self.workflow_instance_id, input_prompt='Please input examples if you have, input "None" if you do not have:')
        content = input['messages'][-1]['content']
        for content_item in content:
            if content_item['type'] == 'text':
                examples = content_item['data']
        if examples == 'None':
            examples = None

        # Collect optional multiple choice options if this is a multiple choice question
        # User can input "None" for standard numerical answer questions
        input = self.input.read_input(workflow_instance_id=self.workflow_instance_id, input_prompt='Please input options if you are doing a multiple choice question, input "None" if you do not have:')
        content = input['messages'][-1]['content']
        for content_item in content:
            if content_item['type'] == 'text':
                options = content_item['data']
        if options == 'None':
            options = None
            
        # Return all collected inputs in a structured format
        inputs = {'query': query, 'examples': examples, 'options': options}
        logging.info(inputs)
        return inputs
