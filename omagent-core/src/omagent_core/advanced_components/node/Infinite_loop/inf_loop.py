from ....engine.node import BaseLoop, Node
from ....memories.ltms.ltm import LTM
from ....engine.workflow.context import BaseWorkflowContext
from ....utils.registry import registry


@registry.register_node()
class InfLoop(BaseLoop):
    loop_body: Node

    def post_loop_exit(self, args: BaseWorkflowContext, ltm: LTM) -> bool:
        return False
