import json_repair
import re
from pathlib import Path
from typing import List
from pydantic import Field

from omagent_core.utils.registry import registry
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.tool_system.manager import ToolManager
from omagent_core.utils.logger import logging

CURRENT_PATH = root_path = Path( __file__ ).parents[ 0 ]


@registry.register_worker()
class SearchSightOrArtifact( BaseWorker ):
    tool_manager: ToolManager

    def _run( self, *args, **kwargs ):

        search_query = "Please consider the user instructions and generate a search query for the web search tool to search for a sight or an artefact based on the user requirements. You must select the web search tool in tool_call. When generating a search query, consider including the name of the attraction or artefact in the information provided. User instructions: {}".format(
            self.stm( self.workflow_instance_id ).get( 'sight_name' )
        )

        execution_status, execution_results = self.tool_manager.execute_task( task=search_query )

        if execution_status == "success":
            self.stm( self.workflow_instance_id )[ "search_results" ] = execution_results
            logging.info( f"search_sight_or_artifact res: {execution_results}" )
        else:
            raise ValueError( "Web search tool execution failed." )
