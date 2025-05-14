from pathlib import Path
from typing import List

from omagent_core.advanced_components.workflow.dnc.schemas.dnc_structure import \
    TaskTree
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.memories.ltms.ltm import LTM
from omagent_core.models.llms.base import BaseLLMBackend, BaseLLM
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
from openai import Stream
from pydantic import Field
from collections.abc import Iterator
from omagent_core.models.llms.prompt.parser import *    
import os

CURRENT_PATH = root_path = Path(__file__).parents[0]

ROOT_PATH = Path(__file__).parents[1]

@registry.register_worker()
class TaskExitMonitor_a4a(BaseWorker):
    def _run(self, *args, **kwargs):    
        
        print ("finished")