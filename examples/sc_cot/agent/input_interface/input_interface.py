from pathlib import Path

from omagent_core.utils.registry import registry
from omagent_core.utils.general import read_image
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.logger import logging

CURRENT_PATH = Path( __file__ ).parents[ 0 ]


@registry.register_worker()
class InputInterface( BaseWorker ):
    """Input interface processor that handles user instructions and image input.
    
    This processor:
    1. Reads user input containing question and image via input interface
    2. Extracts text instruction and image path from the input
    3. Loads and caches the image in workflow storage
    4. Returns the user instruction for next steps
    """

    def _run( self, *args, **kwargs ):
        # Read user input through configured input interface
        user_input = self.input.read_input(
            workflow_instance_id=self.workflow_instance_id,
            input_prompt='Please provide your method (few_shot or zero_shot):'
        )
        messages = user_input[ 'messages' ]
        cot_method = messages[ -1 ][ 'content' ][ 0 ][ 'data' ]

        assert cot_method in [ 'few_shot', 'zero_shot' ], "Invalid method provided"

        if cot_method == 'few_shot':
            user_input = self.input.read_input(
                workflow_instance_id=self.workflow_instance_id,
                input_prompt=
                'If using few_shot method, please provide your examples (in the order of question, reasoning, answer). If using zero_shot, please press enter to skip:'
            )
            messages = user_input[ 'messages' ]
            message = messages[ -1 ][ 'content' ]

            assert len( message ) % 3 == 0, "Invalid number of examples provided"
            cot_examples = [
                {
                    "q": example[ 0 ][ 'data' ],
                    "r": example[ 1 ][ 'data' ],
                    "a": example[ 2 ][ 'data' ]
                } for example in
                [ message[ i : i + 3 ] for i in range( 0, len( message ), 3 ) ]
            ]
        else:
            cot_examples = []

        user_input = self.input.read_input(
            workflow_instance_id=self.workflow_instance_id,
            input_prompt='Please provide your question:'
        )
        messages = user_input[ 'messages' ]
        query = messages[ -1 ][ 'content' ][ 0 ][ 'data' ]

        logging.info(
            f"InputInterface: query={query}, cot_method={cot_method}, cot_examples={cot_examples}"
        )

        return {
            'query': query,
            'cot_method': cot_method,
            'cot_examples': cot_examples
        }
