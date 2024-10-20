from ....engine.node import BaseLoop, Node
from ....memories.ltms.ltm import LTM
from ....engine.workflow.context import BaseWorkflowContext
from ....utils.registry import registry


@registry.register_node()
class DnCLoop(BaseLoop):
    loop_body: Node

    def post_loop_exit(self, args: BaseWorkflowContext, ltm: LTM) -> bool:
        # self.stm.image_cache.clear()
        if args.task.status == "failed":
            return True
        elif args.task.children != []:
            args.task = args.task.children[0]
            return False
        elif args.task.next_sibling_task() is not None:
            args.task = args.task.next_sibling_task()
            return False
        else:
            if args.task.parent is None:
                return True
            elif args.task.parent.next_sibling_task() is None:
                return True
            else:
                args.task = args.task.parent.next_sibling_task()
                return False
