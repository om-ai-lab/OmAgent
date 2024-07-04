from pathlib import Path

from omagent_core.core.node.dnc.interface import DnCInterface
from omagent_core.core.node.dnc.schemas import AgentTask
from omagent_core.handlers.log_handler.logger import logging
from omagent_core.utils.build import Builder
from omagent_core.utils.registry import registry


def run_agent(task):
    logging.init_logger("omagent", "omagent", level="INFO")
    registry.import_module(project_root=Path(__file__).parent, custom=["./engine"])
    bot_builder = Builder.from_file("workflows/video_understanding")
    input = DnCInterface(bot_id="1", task=AgentTask(id=0, task=task))

    bot_builder.run_bot(input)
    return input.last_output


if __name__ == "__main__":
    run_agent("")
