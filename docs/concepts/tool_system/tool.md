# Tool

OmAgent's tool system is a robust and flexible framework that allows developers to create, configure, register, and invoke various tools seamlessly. Tools in OmAgent are modular components that perform specific tasks, enabling the intelligent agent to interact with different services and perform complex operations.  

## Building a Tool

### Key Components of a Tool
To create a new tool in OmAgent, you need to define a class that inherits from `BaseTool` or one of its subclasses. This class should implement the necessary methods to perform its intended functionality.

- **Description**: A string that describes what the tool does.
- **Arguments Schema (`ArgSchema`)**: Defines the input parameters required by the tool.
- **Execution Methods**: 
  - `_run`: Synchronous execution.
  - `_arun`: Asynchronous execution.

### Input Parameters Schema

Configuration involves defining the input parameters that the tool requires and any additional settings it might need. This is typically defined with your tool class in json format.
There are four attributes in each argument in the `ArgSchema`:
- `description`: A string that describes what the tool does.
- `type`: The type of the argument. Support `string`, `integer`, `number`, `boolean`.
- `enum`: A list of allowed values for the argument.
- `required`: A boolean that indicates whether the argument is required

Here is an example of the `ArgSchema` for a tool that performs web search:
```python
ARGSCHEMA = {
    "search_query": {"type": "string", "description": "The search query."},
    "goals_to_browse": {
        "type": "string",
        "description": "What's you want to find on the website returned by search. If you need more details, request it in here. Examples: 'What is latest news about deepmind?', 'What is the main idea of this article?'",
    },
    "region": {
        "type": "string",
        "description": "The region code of the search, default to `en-US`. Available regions: `en-US`, `zh-CN`, `ja-JP`, `de-DE`, `fr-FR`, `en-GB`.",
        "required": True,
    },
    "num_results": {
        "type": "integer",
        "description": "The page number of results to return, default is 1, maximum is 3.",
        "required": True,
    },
}
```

### Registering a Tool
Use the `registry.register_tool()` decorator to register your tool so that it can be instantiated when building a worker. See [registry](./registry.md) for more details about the registry system.

## Tool Manager

The `ToolManager` class is responsible for managing and executing tools. It handles tool initialization, execution, and schema generation.

### Initialization
You can initialize the `ToolManager` with multiple ways:
- Initialize with a list of tool class names or instances or configurations.
  ```python
  tool_manager = ToolManager(tools=["Calculator"])
  tool_manager = ToolManager(tools=[Calculator()])
  tool_manager = ToolManager(tools=[{"name": "Calculator", "description": "Calculator tool."}])
  ```
- Initialize with a dictionary of key-value pairs, where the key is the tool name and the value is the tool instance or configuration.
```python
tool_manager = ToolManager(tools={"my_calculator": Calculator()})
tool_manager = ToolManager(tools={"my_calculator": {"name": "Calculator", "description": "Calculator tool."}})
```
Also, you can initialize the `ToolManager` with a yaml file. The ToolManager will be instantiated when building a worker.
```yaml
tools:
    - Calculator
    - CodeInterpreter
    - ReadFileContent
    - WriteFileContent
    - ShellTool
    - name: WebSearch
      bing_api_key: ${env|bing_api_key, microsoft_bing_api_key}
      llm: ${sub|text_res}

```
If you want the ToolManger to decide which tool to use and generate the corresponding inputs, you should also provide a llm with prompts to the ToolManager.

### Execution
Tools can be invoked using the `ToolManager`. Here's how to execute a tool with a given tool name and arguments:

```python
tool_manager = ToolManager()
result = tool_manager.execute("Calculator", {"code": "print(2 + 3)"})
print(result)
```
The ```ToolManager``` will retrieve the corresponding tool, validate the input arguments and execute the tool.
Another way to execute a tool is use the `execute_task` method. You can provide a task and let the ToolManager decide which tool to use and generate the corresponding inputs.
```python
tool_manager = ToolManager()
result = tool_manager.execute_task("Calculate the result of 2 + 3.")
```