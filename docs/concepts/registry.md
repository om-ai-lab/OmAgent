# Register

The Registry module is a powerful tool for managing and organizing different types of modules in your application. It supports registration and retrieval of various categories like prompts, LLMs, workers, tools, encoders, connectors, and components.

## Registration
You can register classes using either decorators or direct registration:
```python
from omagent_core.utils.registry import registry

# Using decorator (recommended)
@registry.register_node()
class MyNode:
    name = "MyNode"
    
# Or with a custom name
@registry.register_tool(name="custom_tool_name")
class MyTool:
    pass

# Direct registration
class MyLLM:
    pass
registry.register("llm", "my_llm")(MyLLM)
```


## Retrieval
Retrieve registered modules using the get methods:
```python
# Get registered modules
my_node = registry.get_node("MyNode")
my_tool = registry.get_tool("custom_tool_name")
my_llm = registry.get("llm", "my_llm")
```


## Auto-Import Feature
The registry can automatically import modules from specified paths:
```python
# Import from default paths
registry.import_module()

# Import from custom project path
registry.import_module("path/to/your/modules")

# Import from multiple paths
registry.import_module([
    "path/to/modules1",
    "path/to/modules2"
])
```
Note: Do use the ```registry.import_module()``` in the main function of your script so that the modules can be registered to python environment before being used.

