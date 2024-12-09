import json_repair
import re
from pathlib import Path
from typing import List
from pydantic import Field

from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.utils.registry import registry
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.prompt.parser import StrParser
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.utils.logger import logging

CURRENT_PATH = root_path = Path( __file__ ).parents[ 0 ]


@registry.register_worker()
class QuerySightOrArtifact( BaseLLMBackend, BaseWorker ):
    llm: OpenaiGPTLLM
    prompts: List[ PromptTemplate ] = Field(
        default=[
            PromptTemplate.from_file( CURRENT_PATH.joinpath( "sys_prompt.prompt" ), role="system" ),
            PromptTemplate.from_file( CURRENT_PATH.joinpath( "user_prompt.prompt" ), role="user" ),
        ]
    )

    def _extract_from_result( self, result: str ) -> dict:
        try:
            pattern = r"```json\s+(.*?)\s+```"
            match = re.search( pattern, result, re.DOTALL )
            if match:
                return json_repair.loads( match.group( 1 ) )
            else:
                return json_repair.loads( result )
        except Exception as error:
            raise ValueError( "LLM generation is not valid." )

    def _run( self, *args, **kwargs ):
        # Determine whether the image is a scenic spot or cultural relic, and obtain the name of the scenic spot or cultural relic

        chat_complete_res = self.simple_infer( image=self.stm( self.workflow_instance_id )[ 'image_cache' ].get( '<image_0>' ) )
        content = chat_complete_res[ "choices" ][ 0 ][ "message" ].get( "content" )
        content = self._extract_from_result( content )

        if content.get( 'is_sight' ):
            self.stm( self.workflow_instance_id )[ "sight_name" ] = content.get( 'sight_name' )
            logging.info( f"query_sight_or_artifact res: {content}, sight_name: {self.stm( self.workflow_instance_id ).get('sight_name')}" )
            return { "switch_case_value": 1}
        else:
            logging.info( f"query_sight_or_artifact res: {content}" )
            self.callback.send_answer( agent_id=self.workflow_instance_id, msg="The input image is neither a sight nor an artefact." )
            self.stm( self.workflow_instance_id ).clear()
            return { "switch_case_value": 0}
