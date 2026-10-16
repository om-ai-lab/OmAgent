# Import required modules and components
import os
os.environ["OMAGENT_MODE"] = "lite"
from pathlib import Path

from agent.conclude.conclude import Conclude
from agent.video_preprocessor.video_preprocess import VideoPreprocessor
from agent.video_qa.qa import VideoQA
from omagent_core.advanced_components.workflow.dnc.workflow import DnCWorkflow
from omagent_core.clients.devices.cli import DefaultClient
from omagent_core.engine.automator.task_handler import TaskHandler
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.do_while_task import (DnCLoopTask,
                                                             InfiniteLoopTask)
from omagent_core.engine.workflow.task.set_variable_task import SetVariableTask
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.engine.workflow.task.switch_task import SwitchTask
from omagent_core.utils.build import build_from_file
from omagent_core.utils.container import container
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry

logging.init_logger("omagent", "omagent", level="INFO")

# Set current working directory path
CURRENT_PATH = root_path = Path(__file__).parents[0]

# Import registered modules
registry.import_module(project_path=CURRENT_PATH.joinpath("agent"))

# Load container configuration from YAML file
container.register_stm("SharedMemSTM")
container.register_ltm(ltm="VideoMilvusLTM")
container.from_config(CURRENT_PATH.joinpath("container.yaml"))

# Initialize simple VQA workflow
workflow = ConductorWorkflow(name="video_understanding")

# 1. Video preprocess task for video preprocessing
video_preprocess_task = simple_task(
    task_def_name=VideoPreprocessor, task_reference_name="video_preprocess"
)

# 2. Video QA task for video QA
video_qa_task = simple_task(
    task_def_name=VideoQA,
    task_reference_name="video_qa",
    inputs={
        "video_md5": video_preprocess_task.output("video_md5"),
        "video_path": video_preprocess_task.output("video_path"),
        "instance_id": video_preprocess_task.output("instance_id"),
    },
)

dnc_workflow = DnCWorkflow()
dnc_workflow.set_input(query=video_qa_task.output("query"))

# 7. Conclude task for task conclusion
conclude_task = simple_task(
    task_def_name=Conclude,
    task_reference_name="task_conclude",
    inputs={
        "dnc_structure": dnc_workflow.dnc_structure,
        "last_output": dnc_workflow.last_output,
    },
)


# Configure workflow execution flow: Input -> Initialize global variables -> DnC Loop -> Conclude
workflow >> video_preprocess_task >> video_qa_task >> dnc_workflow >> conclude_task

# Register workflow
workflow.register(overwrite=True)

# Initialize and start app client with workflow configuration
cli_client = DefaultClient(
    interactor=workflow, config_path="examples/video_understanding/configs"
)
cli_client.start_interactor()
