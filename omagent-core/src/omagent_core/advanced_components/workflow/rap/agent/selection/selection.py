from pathlib import Path
from typing import List
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.utils.registry import registry
from pydantic import Field
from ...schemas.rap_structure import SearchTree, MCTS

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class Selection(BaseWorker):
    """Selection worker that implements MCTS selection phase"""

    def _run(self, *args, **kwargs):
        depth_limit = kwargs.get('depth_limit', 5)

        # Get tree from STM
        assert self.stm(self.workflow_instance_id).get('data_input', None) is not None
        
        data_input = self.stm(self.workflow_instance_id)['data_input']
        task = self.stm(self.workflow_instance_id)['task']

        # Initialize tree if needed
        if self.stm(self.workflow_instance_id).get('tree', None) is None:
            self.stm(self.workflow_instance_id)['tree'] = SearchTree(data_input)
            self.stm(self.workflow_instance_id)['in_simulation'] = False
            
        tree = self.stm(self.workflow_instance_id)['tree']

        # Selection phase
        selected_path = []
        node = tree.root
        while True:
            selected_path.append(node)
            if node.children is None or len(node.children) == 0 or node.depth >= depth_limit:
                break
            node = MCTS.uct_select(node)

        # Log selected path
        info_str = '\n'.join([n.state for n in selected_path])
        self.callback.send_answer(self.workflow_instance_id, msg=info_str)
        
        # Store selected path
        self.stm(self.workflow_instance_id)['selected_path'] = selected_path

        return {"selected_path": selected_path} 