# Import required modules and components
import os
from pathlib import Path

from agent.conclude.webpage_conclude import WebpageConclude
from agent.video_preprocessor.webpage_vp import WebpageVideoPreprocessor
from agent.video_qa.webpage_qa import WebpageVideoQA
from agent.client.webpage import WebpageClient

from omagent_core.advanced_components.workflow.dnc.workflow import DnCWorkflow
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.utils.container import container
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry

logging.init_logger("omagent", "omagent", level="INFO")

# Set current working directory path
CURRENT_PATH = root_path = Path(__file__).parents[0]

# Import registered modules
registry.import_module(project_path=CURRENT_PATH.joinpath("agent"))

# Load container configuration from YAML file
container.register_stm("RedisSTM")
container.register_ltm(ltm="VideoMilvusLTM")
container.from_config(CURRENT_PATH.joinpath("container.yaml"))

# Initialize simple VQA workflow
workflow = ConductorWorkflow(name="webpage_video_understanding")
process_workflow = ConductorWorkflow(name="webpage_process_video_understanding")
# 1. Video preprocess task for video preprocessing
video_preprocess_task = simple_task(
    task_def_name=WebpageVideoPreprocessor,
    task_reference_name="webpage_video_preprocess",
    inputs={"video_path": process_workflow.input("video_path")}
)

# 2. Video QA task for video QA
video_qa_task = simple_task(
    task_def_name=WebpageVideoQA,
    task_reference_name="webpage_video_qa",
    inputs={
        "video_md5": workflow.input("video_md5"),
        "video_path": workflow.input("video_path"),
        "instance_id": workflow.input("instance_id"),
        "question": workflow.input("question"),
    },
)

dnc_workflow = DnCWorkflow()
dnc_workflow.set_input(query=video_qa_task.output("query"))
# 7. Conclude task for task conclusion
conclude_task = simple_task(
    task_def_name=WebpageConclude,
    task_reference_name="webpage_task_conclude",
    inputs={
        "dnc_structure": dnc_workflow.dnc_structure,
        "last_output": dnc_workflow.last_output,
    },
)

# Configure workflow execution flow: Input -> Initialize global variables -> DnC Loop -> Conclude
process_workflow >> video_preprocess_task
workflow >> video_preprocess_task >> video_qa_task >> dnc_workflow >> conclude_task

# Register workflow
workflow.register(overwrite=True)
process_workflow.register(overwrite=True)

# Initialize and start app client with workflow configuration
cli_client = WebpageClient(
    interactor=workflow, processor=process_workflow, config_path="examples/video_understanding/webpage_configs"
)
cli_client.start_interactor()
