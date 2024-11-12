# Workflow
Workflow is the top-level object in Omagent. It contains a list of tasks and the dependencies between them.  

## Creating a Workflow
You can create a workflow by instantiating the `ConductorWorkflow` class.
```python
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow

workflow = ConductorWorkflow(name='test_workflow')
```

## Adding Tasks to a Workflow
You can add tasks to a workflow by using ```add``` method. (See [task](./task.md) for more details about tasks)
```python
workflow.add(task)
```
There is a shortcut operator `>>` for this method.
```python
workflow >> task
```
Also, you can chaining the tasks as follows:
```python
workflow >> task1 >> task2 >> task3
```
There is a simple way to create fork-join tasks.
```python
workflow >> task1 >> [task2, task3, task4] >> task5
```
There is also a simple way to define a switch task.
```python
workflow >> switch_task >> {'case1': task1, 'case2': task2, 'default': task3} #  default is for a scenario that the result does not correspond to any specified case
```
Note that the switch_task **MUST** output ```switch_case_value``` as indicator for branching.

You can use a workflow as a task in another workflow.
```python
sub_workflow >> task1 >> task2
workflow >> task3 >> sub_workflow >> task4
```

## Registering a Workflow
You can register a workflow by using ```register``` method.
```python
workflow.register(overwrite=True)
```
After registering, you can see the workflow in the Conductor UI (default at http://localhost:5001/workflowDefs).

## Running a Workflow
You can start a workflow instance and send input to it by using ```start_workflow_with_input``` method.
```python
workflow_execution_id = workflow.start_workflow_with_input(workflow_input={'name': 'Lu'})
```

## Getting Workflow Status and Result
Since the workflow is a async task, you can get its status and result by using ```get_workflow``` method.
```python
status = workflow.get_workflow(workflow_id=workflow_execution_id).status
result = workflow.get_workflow(workflow_id=workflow_execution_id).output
```