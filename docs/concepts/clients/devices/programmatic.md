# ProgrammaticClient

## Introduction
`ProgrammaticClient` is a client tool designed for executing batch tasks.

## Initialization Parameters
- `processor`: Required parameter, the processor for handling tasks
- `config_path`: Optional parameter, path to the worker configuration file
- `workers`: Optional parameter, list of Worker instances

Note: Either `config_path` or `workers` must be provided.

## Execution Methods
ProgrammaticClient provides two methods for executing batch tasks:

### 1. start_batch_processor
Parallel processing of multiple tasks:
```python
# Usage example
workflow_input_list = []
for i in range(3):
    workflow_input_list.append({
        "id": str(i), 
        "file_path": f"/path/to/test{i}.png"
    })
programmatic_client.start_batch_processor(workflow_input_list=workflow_input_list)
programmatic_client.stop_processor()
```

Features:
- Supports multi-process parallel execution
- Default of 5 processes per worker
- Process count can be adjusted via the `concurrency` parameter in the worker configuration file

### 2. start_processor_with_input
Serial processing of individual tasks:
```python
# Usage example
for i in range(3):
    programmatic_client.start_processor_with_input(
        workflow_input={"id": str(i), "file_path": f"/path/to/test{i}.png"}
    )
programmatic_client.stop_processor()
```

Features:
- Executes one task at a time
- Waits for the current task to complete before executing the next one

## Parameter Passing
To pass parameters during execution, you need to:
1. Define the corresponding parameters in the worker's `_run` method
2. Specify parameter sources when defining the task

Example code:
```python
@registry.register_worker()
class SimpleTest(BaseWorker):
    def _run(self, id: str, file_path: str):
        print("id:", id)
        print("file_path:", file_path)
        # do something

# Define task
task1 = simple_task(
    task_def_name="SimpleTest",
    task_reference_name="simple_test",
    inputs={
        "id": workflow.input("id"),
        "file_path": workflow.input("file_path")
    }
)

workflow >> task1
```