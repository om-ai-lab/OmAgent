from typing import Type, Set, Union, List
from pathlib import Path
import yaml
from omagent_core.base import BotBase
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.utils.registry import registry
from omagent_core.engine.workflow.task.task import TaskInterface
from omagent_core.engine.workflow.task.simple_task import SimpleTask
from omagent_core.engine.workflow.task.switch_task import SwitchTask
from omagent_core.engine.workflow.task.fork_task import ForkTask
from omagent_core.engine.workflow.task.do_while_task import DoWhileTask
from omagent_core.engine.workflow.conductor_workflow import InlineSubWorkflowTask
from omagent_core.utils.container import container


# recursive processing of sub-workflows
def process_tasks(
    tasks: List[TaskInterface],
    worker_list: Set[str] = set(),
) -> Set[str]:
    for task in tasks:
        if isinstance(task, SimpleTask):
            worker_list.add(task.name)
        elif isinstance(task, SwitchTask):
            if task._default_case:
                process_tasks(task._default_case, worker_list)
            if task._decision_cases:
                process_tasks(list(task._decision_cases.values()), worker_list)

        elif isinstance(task, ForkTask):
            if task._forked_tasks:
                process_tasks(task._forked_tasks, worker_list)
        elif isinstance(task, DoWhileTask):
            if task._loop_over:
                process_tasks(task._loop_over, worker_list)
        elif isinstance(task, InlineSubWorkflowTask):
            # recursive compilation of sub-workflows
            process_tasks(task._workflow._tasks, worker_list)
        else:
            raise ValueError(f"Unsupported task type {type(task)}")

    return worker_list


def compile(
    workflow: ConductorWorkflow,
    output_path: Union[str, Path],
    overwrite: bool = False,
    description: bool = True,
    env_var: bool = True,
) -> str:
    """compile the workflow, generate the config files and register the workflow to the conductor server

    Args:
        workflow: ConductorWorkflow instance
        output_path: The path to save the compiled configs
        overwrite: Whether to overwrite the existing workflow
    """
    output_path = Path(output_path) if isinstance(output_path, str) else output_path
    worker_config = {}

    worker_list = process_tasks(workflow._tasks)

    for worker_name in worker_list:
        worker = registry.get_worker(worker_name)
        worker_config[worker_name] = worker.get_config_template(
            description=description, env_var=env_var
        )

    print(worker_config)
    worker_config = yaml.dump(
        worker_config, allow_unicode=True, sort_keys=False
    )

    workflow.register(overwrite=overwrite)
    print(
        f"see the workflow definition here: {container.get_connector('conductor_config').ui_host}/workflowDef/{workflow.name}\n"
    )
    with open(output_path / "worker.yaml", "w") as f:
        f.write(worker_config)
        
    container_config = container.compile_config()
    if container_config['connectors']:
        with open(output_path / "connectors.yaml", "w") as f:
            f.write(yaml.dump(container_config['connectors'], sort_keys=False, allow_unicode=True))
    if container_config['components']:
        with open(output_path / "components.yaml", "w") as f:
            f.write(yaml.dump(container_config['components'], sort_keys=False, allow_unicode=True))

    return {"worker_config": worker_config}
