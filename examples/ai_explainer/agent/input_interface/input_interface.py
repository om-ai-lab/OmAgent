from pathlib import Path

from omagent_core.utils.registry import registry
from omagent_core.utils.general import read_image
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.logger import logging

CURRENT_PATH = Path( __file__ ).parents[ 0 ]


@registry.register_worker()
class InputInterface( BaseWorker ):

    def _run( self, *args, **kwargs ):
        # Read user input through configured input interface
        user_input = self.input.read_input(
            workflow_instance_id=self.workflow_instance_id, input_prompt='Please input a image of sight or artifact.'
        )

        # Extract text and image content from input message
        content = user_input[ 'messages' ][ -1 ][ 'content' ]
        for content_item in content:
            if content_item[ 'type' ] == 'image_url':
                image_path = content_item[ 'data' ]

        try:
            img = read_image( input_source=image_path )
            image_cache = {'<image_0>' : img}
            self.stm( self.workflow_instance_id )[ 'image_cache' ] = image_cache
        except Exception as e:
            pass

        return
