# Import required modules and components
import os
from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.webpage.client import WebpageClient
from omagent_core.utils.logger import logging
from omagent_core.engine.workflow.task.set_variable_task import SetVariableTask
from omagent_core.engine.workflow.task.switch_task import SwitchTask
from omagent_core.engine.workflow.task.do_while_task import DnCLoopTask
from agent.input_interface.dnc_input_interface import DnCInputIterface
logging.init_logger("omagent", "omagent", level="INFO")


# Set current working directory path
CURRENT_PATH = root_path = Path(__file__).parents[0]

# Import registered modules
registry.import_module()

# Load container configuration from YAML file
container.register_stm("RedisSTM")
container.from_config(CURRENT_PATH.joinpath('container.yaml'))

# Initialize simple VQA workflow
workflow = ConductorWorkflow(name='general_dnc')

# Configure workflow tasks:
# 1. Input interface for user interaction
client_input_task = simple_task(task_def_name='DnCInputIterface', task_reference_name='dnc_input_interface')

# 2. Initialize set variable task for global workflow variables
init_set_variable_task = SetVariableTask(task_ref_name='set_variable_task', input_parameters={'agent_task': client_input_task.output('agent_task'), 'last_output': client_input_task.output('last_output')})

# 3. Conqueror task for task generation and update global workflow variables
conqueror_task = simple_task(task_def_name='TaskConqueror', task_reference_name='task_conqueror', inputs={'agent_task': '${workflow.variables.agent_task}', 'last_output': '${workflow.variables.last_output}'})
conqueror_update_set_variable_task = SetVariableTask(task_ref_name='conqueror_update_set_variable_task', input_parameters={'agent_task': '${task_conqueror.output.agent_task}', 'last_output': '${task_conqueror.output.last_output}'})

# 4. Divider task for task division and update global workflow variables
divider_task = simple_task(task_def_name='TaskDivider', task_reference_name='task_divider', inputs={'agent_task': conqueror_task.output('agent_task'), 'last_output': conqueror_task.output('last_output')})
divider_update_set_variable_task = SetVariableTask(task_ref_name='divider_update_set_variable_task', input_parameters={'agent_task': '${task_divider.output.agent_task}', 'last_output': '${task_divider.output.last_output}'})

# 5. Rescue task for task rescue
rescue_task = simple_task(task_def_name='TaskRescue', task_reference_name='task_rescue', inputs={'agent_task': conqueror_task.output('agent_task'), 'last_output': conqueror_task.output('last_output')})

# 6. Conclude task for task conclusion
conclude_task = simple_task(task_def_name='Conclude', task_reference_name='task_conclude', inputs={'agent_task': '${task_exit_monitor.output.agent_task}', 'last_output': '${task_exit_monitor.output.last_output}'})

# 7. Switch task for task routing
switch_task = SwitchTask(task_ref_name='switch_task', case_expression=conqueror_task.output('switch_case_value'))
switch_task.default_case([conqueror_update_set_variable_task])
switch_task.switch_case("complex", [divider_task, divider_update_set_variable_task])
switch_task.switch_case("failed", rescue_task)

# 8. Task exit monitor task for task exit monitoring and update global workflow variables
task_exit_monitor_task = simple_task(task_def_name='TaskExitMonitor', task_reference_name='task_exit_monitor', inputs={'agent_task': '${workflow.variables.agent_task}', 'last_output': '${workflow.variables.last_output}'})
post_set_variable_task = SetVariableTask(task_ref_name='post_set_variable_task', input_parameters={'agent_task': '${task_exit_monitor.output.agent_task}', 'last_output': '${task_exit_monitor.output.last_output}'})

# 9. DnC loop task for task loop
dncloop_task = DnCLoopTask(task_ref_name='dncloop_task', tasks=[conqueror_task, switch_task], post_loop_exit=[task_exit_monitor_task, post_set_variable_task])

# Configure workflow execution flow: Input -> Initialize global variables -> DnC Loop -> Conclude
workflow >> client_input_task >> init_set_variable_task >> dncloop_task >> conclude_task

# Register workflow
workflow.register(overwrite=True)

# Initialize and start app client with workflow configuration
config_path = CURRENT_PATH.joinpath('configs')
agent_client = WebpageClient(interactor=workflow, config_path=config_path, workers=[DnCInputIterface()])
agent_client.start_interactor()
