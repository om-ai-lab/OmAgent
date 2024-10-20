from pathlib import Path

from omagent_core.engine.workflow.context import BaseWorkflowContext
from omagent_core.engine.task.agent_task import AgentTask
from omagent_core.utils.logger import logging
from omagent_core.utils.build import Builder
from omagent_core.utils.registry import registry


def run_agent(task):
    logging.init_logger("omagent", "omagent", level="INFO")
    registry.import_module(project_root=Path(__file__).parent, custom=["./examples"])
    bot_builder = Builder.from_file("examples/video_understanding")
    input = BaseWorkflowContext(bot_id="1", task=AgentTask(id=0, task=task))

    bot_builder.run_bot(input)
    return input.last_output


if __name__ == "__main__":
    run_agent("")
