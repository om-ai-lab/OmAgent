# Worker
Worker is the basic unit of computation in OmAgent. It is responsible for executing tasks and generating outputs.  
## How to define a worker  
The most basic worker can be created like this:
```python
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry

@registry.register_worker()
class MyWorker(BaseWorker):
    def _run(self, *args, **kwargs):
        # Implement your business logic here
        return {"result": "some_value"}
```
By inheriting from `BaseWorker`, you can define your own worker. The worker will be registered with the name of the class. Normally, use `@registry.register_worker()` to register the worker so that it can build from configurations. See [registry](./registry.md) for more details.

### 1. Parameter Handling
You can define typed parameters that are json serializable, and return in key-value format:
```python
@registry.register_worker()
class ParameterWorker(BaseWorker):
    def _run(self, name: str, age: int):
        # Parameters will be automatically extracted
        return {
            "message": f"Hello {name}, you are {age} years old"
        }
```

### 2. Integration
You can integrate workers with other libraries to extend the functionality. A most common case is to integrate with LLMs. Here is an example of how:
```python
@registry.register_worker()
class LLMWorker(BaseLLMBackend, BaseWorker)
    llm: OpenaiGPTLLM
    output_parser: StrParser
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_template(template="Your prompt here")
        ]
    )

    def _run(self, *args, **kwargs):
        return self.simple_infer()
```

### 3. Configuration Fields
You can configure worker behavior using Pydantic Fields to set default values:
```python
@registry.register_worker()
class ConfigurableWorker(BaseWorker):
    poll_interval: float = Field(default=100)  # Polling interval in milliseconds
    domain: str = Field(default=None)          # Workflow domain
    concurrency: int = Field(default=5)        # Concurrency level
```
Note: do not use ```alias``` in the field definition.

### 4. Async Support
Workers can be asynchronous:
```python
@registry.register_worker()
class AsyncWorker(BaseWorker):
    async def _run(self, *args, **kwargs):
        async def count_task(i):
            await asyncio.sleep(1)
            print(f'Task {i} completed!')
            return i

        tasks = [count_task(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        return {"result": "async operation completed"}
```

## Configuration and build  
Workers can be configured and built from YAML or JSON configuration files. You not only can set the parameters, but the recursive dependencies.
### 1. Worker Configuration Structure
Here's the basic structure:
```yaml
name: LLMWorker
llm:
    name: OpenaiGPTLLM
    model_id: gpt-4o
    api_key: sk-proj-...
    endpoint: https://api.openai.com/v1
    temperature: 0
    vision: true
output_parser:
    name: StrParser
```
### 2. Submodule Substitution
You can use the ${sub|**module_name**} to substitute submodules. This is useful when you want to reuse the same submodule in different workers and also keep the configuration clean. The **module_name** should be the name of the submodule configuration file.  
For example, you can define the llm_worker.yaml as follows:
```yaml
name: LLMWorker
llm: ${sub|gpt}
output_parser:
    name: StrParser
```
And define the gpt.yaml as follows:
```yaml
name: OpenaiGPTLLM
model_id: gpt-4o
api_key: sk-proj-...
endpoint: https://api.openai.com/v1
temperature: 0
vision: true
```
This is equivalent to the previous LLMWorker example.  
Note: Do not use ```alias``` in the field definition. Do not create Circular reference.

### 3. Environment Variables
You can use the ${env|**env_name**, **default_value**} to substitute environment variables. This is useful when you want to set the parameters dynamically. The **env_name** should be the name of the environment variable. **default_value** is optional, and will be used when the environment variable is not set.
For example, you can define the gpt.yaml as follows:
```yaml
name: OpenaiGPTLLM
model_id: gpt-4o
api_key: ${env| CUSTOM_OPENAI_KEY}
endpoint: ${env| CUSTOM_OPENAI_ENDPOINT, https://api.openai.com/v1}
temperature: 0
vision: true
```
The environment variable name is case-sensitive.

### 4. Default Configuration Fields
Workers have several default configuration fields that can be set:
- **component_stm**: The STM component for the worker. Use any registered component name. Default is the one registered with `register_stm`. Access it via `self.stm`. See [container](./container.md) and [memory](./memory.md) for more details.
- **component_ltm**: The LTM component for the worker. Use any registered component name. Default is the one registered with `register_ltm`. Access it via `self.ltm`. See [container](./container.md) and [memory](./memory.md) for more details.
- **component_callback**: The callback component for the worker. Use any registered component name. Default is the one registered with `register_callback`. Access it via `self.callback`. See [container](./container.md) and [client](./client.md) for more details.
- **component_input**: The input component for the worker. Use any registered component name. Default is the one registered with `register_input`. Access it via `self.input`. See [container](./container.md) and [client](./client.md) for more details.
- **poll_interval**: The poll interval for the worker. Default is 100 milliseconds.
- **domain**: The domain of the workflow. Default is None.
- **concurrency**: The concurrency of the worker. Default is 5.
  
### 5. Build from Configurations  
The worker instances can be built from configurations by using the ```build_from_file``` function from omagent_core.utils.build. Here's how it works:
```python
from omagent_core.utils.build import build_from_file

# Load worker configs from a directory
worker_config = build_from_file('path/to/config/directory')
```
Note: You must provide a ```workers``` directory in the configuration path which contains all configurations for the workers. 

## Run workers
OmAgent provides a TaskHandler class to manage worker instance creation and management. Here's how to use TaskHandler:
```python
from omagent_core.engine.automator.task_handler import TaskHandler

task_handler = TaskHandler(worker_config=worker_config, workers=[MyWorker()])
task_handler.start_processes()
task_handler.stop_processes()
```
The `worker_config` parameter accepts a set of worker configurations and launches the corresponding number of processes based on each worker's concurrency attribute value.  

You can also use the `workers` parameter to directly pass in instantiated worker objects. Instances of these workers are deepcopied based on the concurrency setting. If your worker instances contain objects that cannot be deepcopied, set the instance's concurrency property to 1 and actively expand the concurrency count in the workers list.  

Then, use `start_processes` to start all workers and `stop_processes` to stop all workers.

## Important Notes
- Always use the @registry.register_worker() decorator to register the worker
- The ```_run``` method is mandatory and contains your core logic
- Return values should be a dictionary with serializable values
- Worker behavior can be configured using Fields
- Both synchronous and asynchronous operations are supported
- The ```self.workflow_instance_id``` is automatically available in the worker context
  
## Best Practices
- Keep workers focused on a single responsibility
- Use proper type hints for better code clarity
- Implement proper error handling
- Document your worker's expected inputs and outputs
- Use configuration fields for flexible behavior
- Consider using async operations for I/O-bound tasks
