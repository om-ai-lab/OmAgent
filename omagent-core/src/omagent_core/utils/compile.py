from typing import Union
from pathlib import Path
import yaml
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.utils.container import container



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

    workflow.register(overwrite=overwrite)
    print(
        f"see the workflow definition here: {container.get_connector('conductor_config').ui_host}/workflowDef/{workflow.name}\n"
    )

    if not (output_path / "container.yaml").exists():
        container_config = container.compile_config(description=description, env_var=env_var)
        with open(output_path / "container.yaml", "w") as f:
            f.write(yaml.dump(container_config, sort_keys=False, allow_unicode=True))
    else:
        print("container.yaml already exists, skip compiling")
        container_config = yaml.load(open(output_path / "container.yaml", "r"), Loader=yaml.FullLoader)

    return {"container_config": container_config}
