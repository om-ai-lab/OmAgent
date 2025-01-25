from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
from omagent_core.utils.logger import logging
from pathlib import Path

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class COTInputInterface(BaseWorker):

    def _run(self, *args, **kwargs):
        user_input = self.input.read_input(workflow_instance_id=self.workflow_instance_id, input_prompt='Please input your question:')

        question = user_input['messages'][-1]['content'][0]['data']

        self.stm(self.workflow_instance_id)['user_question'] = question

        return {'user_question': question}