from omagent_core.core.node.base import BaseLoop, Node
from omagent_core.handlers.data_handler.ltm import LTM
from omagent_core.schemas.base import BaseInterface
from omagent_core.utils.registry import registry


@registry.register_node()
class InfLoop(BaseLoop):
    loop_body: Node

    def post_loop_exit(self, args: BaseInterface, ltm: LTM) -> bool:
        return False
