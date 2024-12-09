# Task

Task is the basic unit of building workflow. There are two types of tasks: simple task and operator.

## Simple Task
The functionality of simple task is defined by binding it to a [worker](./worker.md).
Here is an example of how to define a simple task:
```python
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.utils.registry import registry

# Define a worker
@registry.register_worker()
class SimpleWorker(BaseWorker):
    def _run(self, my_name: str):
        return {}

# Define a workflow
workflow = ConductorWorkflow(name='my_exp')

# Define a simple task
task = simple_task(task_def_name='SimpleWorker', task_reference_name='ref_name', inputs={'my_name': workflow.input('my_name')})

workflow >> task
```
Specify the task definition name(```task_def_name```) and the task reference name(```task_reference_name```). The task definition name should be the name of the corresponding worker class. The task reference name is used to identify the task in the workflow.
Specify the inputs of the task. Inputs may be either values or references to a workflow's initial inputs or the outputs of preceding tasks.
See [workflow](./workflow.md) for workflow details.

## Operators
Operators are the build-in tasks provided by the workflow engine. They handle the workflow control logic.
### 1. Switch Task
Switch task is used to make a decision based on the value of a given field.
```python
from omagent_core.engine.workflow.task.switch_task import SwitchTask
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.utils.registry import registry

@registry.register_worker()
class SimpleWorker1(BaseWorker):
    def _run(self):
        print('worker1')
        return {}

@registry.register_worker()
class SimpleWorker2(BaseWorker):
    def _run(self):
        print('worker2')
        return {} 

@registry.register_worker()
class SimpleWorker3(BaseWorker):
    def _run(self):
        print('worker3')
        return {} 

workflow = ConductorWorkflow(name='switch_test')

# Create some example tasks (replace with your actual tasks)
task1 = simple_task(task_def_name='SimpleWorker1', task_reference_name='ref_name1')
task2 = simple_task(task_def_name='SimpleWorker2', task_reference_name='ref_name2')
task3 = simple_task(task_def_name='SimpleWorker3', task_reference_name='ref_name3')

# 1. Create a switch task with a value-based condition
switch = SwitchTask(
    task_ref_name="my_switch",
    case_expression=workflow.input('switch_case_value'),  # This will evaluate the switch_case_value from workflow input
)

# 2. Add cases
switch.switch_case("w1", [task1])
switch.switch_case("w2", [task2])

# 3. Add default case (optional)
switch.default_case([task3])

workflow >> switch

workflow.register(overwrite=True)
```
This will create a basic workflow with a switch task shown below. (You can check the workflow definition at Conductor UI default at http://localhost:5001/workflowDefs).
<p align="center">
  <img src="../../images/switch_task.png" width="500"/>
</p>  
You can also chaining the switch cases as follows:  

```python
switch.switch_case("w1", [task1]).switch_case("w2", [task2]).default_case([task3])
```

### 2. Fork-Join Task
The fork-join task is used to execute multiple tasks in parallel.
```python
from omagent_core.engine.workflow.task.fork_task import ForkTask
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.utils.registry import registry


@registry.register_worker()
class SimpleWorker1(BaseWorker):
    def _run(self):
        print("worker1")
        return {}


@registry.register_worker()
class SimpleWorker2(BaseWorker):
    def _run(self):
        print("worker2")
        return {}


@registry.register_worker()
class SimpleWorker3(BaseWorker):
    def _run(self):
        print("worker3")
        return {}


# Create the main workflow
workflow = ConductorWorkflow(name="fork_join_test")

# Create tasks for parallel execution
task1 = simple_task(task_def_name="SimpleWorker1", task_reference_name="parallel_task1")
task2 = simple_task(task_def_name="SimpleWorker2", task_reference_name="parallel_task2")
task3 = simple_task(task_def_name="SimpleWorker3", task_reference_name="parallel_task3")

# Create parallel execution paths
path1 = [task1]  # First parallel path
path2 = [task2]  # Second parallel path
path3 = [task3]  # Third parallel path

# Create the fork task with multiple parallel paths
fork_task = ForkTask(
    task_ref_name="parallel_execution",
    forked_tasks=[path1, path2, path3],
    # The join will wait for the last task in each path
    join_on=["parallel_task1", "parallel_task2", "parallel_task3"]
)

# Add the fork task to the workflow
workflow.add(fork_task)

workflow.register(overwrite=True)
```
This will create a basic workflow with a fork-join task shown below.
<p align="center">
  <img src="../../images/fork_task.png" width="500"/>
</p>  

### 3. Do-While Task
The Do-While task is used to execute a loop.
```python
from omagent_core.engine.workflow.task.do_while_task import DoWhileTask
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.utils.registry import registry


@registry.register_worker()
class SimpleWorker1(BaseWorker):
    def _run(self):
        print("worker1")
        return {}

@registry.register_worker()
class SimpleWorker2(BaseWorker):
    def _run(self):
        print("worker2")
        return {}

@registry.register_worker()
class TaskExitMonitor(BaseWorker):
    """
    This worker is used to monitor the exit flag of the task.
    """
    def _run(self):
        print("task exit monitor")
        # write some code here to decide whether to exit the loop
        # if exit_flag is true, exit the loop
        # if exit_flag is false, continue the loop
        return {"exit_flag": True/False}

# Create the main workflow
workflow = ConductorWorkflow(name="do_while_test")

# Create tasks for loop body
task1 = simple_task(task_def_name="SimpleWorker1", task_reference_name="loop_body_task1")
task2 = simple_task(task_def_name="SimpleWorker2", task_reference_name="loop_body_task2")
task_exit_monitor = simple_task(task_def_name="TaskExitMonitor", task_reference_name="task_exit_monitor")

# create the loop condition, this is the javascript expression that evaluates to True or False
loop_condition = f" if ( $.task_exit_monitor['exit_flag'] == true) {{ false; }} else {{ true; }}"

# Create the loop_task
loop_task = DoWhileTask(task_ref_name="loop_task", termination_condition=loop_condition, tasks=[task1, task2, task_exit_monitor])

# Add the loop task to the workflow
workflow.add(loop_task)

workflow.register(overwrite=True)
```
This will create a basic workflow with a do-while task shown below.
<p align="center">
  <img src="../../images/do_while_task.png" width="500"/>
</p>  