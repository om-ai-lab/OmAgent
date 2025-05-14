import os
os.environ["OMAGENT_MODE"] = "lite"

from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.utils.container import container
from omagent_core.utils.logger import logging

logging.init_logger("omagent", "omagent", level="INFO")

from pathlib import Path

from omagent_core.clients.devices.cli import DefaultClient

CURRENT_PATH = Path(__file__).parents[0]

from omagent_core.utils.registry import registry

registry.import_module(project_path=CURRENT_PATH.joinpath("agent"))

import os
import sys

sys.path.append(os.path.abspath(CURRENT_PATH.joinpath("../../../")))

from omagent_core.engine.workflow.task.do_while_task import DoWhileTask

from examples.step3_outfit_with_loop.agent.outfit_decider.outfit_decider import \
    OutfitDecider
from examples.step3_outfit_with_loop.agent.outfit_qa.outfit_qa import OutfitQA

# Register storage components
container.register_stm("SharedMemSTM")
container.register_ltm("MilvusLTM")

# Load container configuration
container.from_config(CURRENT_PATH.joinpath("container.yaml"))

# Create main workflow
workflow = ConductorWorkflow(name="step4_outfit_recommendation")

# Initialize QA task to gather user preferences
task1 = simple_task(task_def_name="OutfitQA", task_reference_name="outfit_qa")

# Initialize decision task to evaluate QA responses
task2 = simple_task(task_def_name="OutfitDecider", task_reference_name="outfit_decider")

# Initialize outfit generation task
task3 = simple_task(
    task_def_name="OutfitGeneration", task_reference_name="outfit_generation"
)

# Initialize conclusion task with outfit generation output
task4 = simple_task(
    task_def_name="OutfitConclusion",
    task_reference_name="outfit_conclusion",
    inputs={"proposed_outfit": task3.output("proposed_outfit")},
)

# Create iterative QA loop that continues until a positive decision is reached
outfit_qa_loop = DoWhileTask(
    task_ref_name="outfit_loop",
    tasks=[task1, task2],
    termination_condition='if ($.outfit_decider["decision"] == true){false;} else {true;}  ',
)

# Define workflow sequence
workflow >> outfit_qa_loop >> task3 >> task4

# Register workflow with conductor
workflow.register(True)

# Initialize and run CLI client
config_path = CURRENT_PATH.joinpath("configs")
cli_client = DefaultClient(interactor=workflow, config_path=config_path)
cli_client.start_interactor()
