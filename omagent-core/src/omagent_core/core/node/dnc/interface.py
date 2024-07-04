from ....schemas.base import BaseInterface
from .schemas import AgentTask


class DnCInterface(BaseInterface):
    task: AgentTask
