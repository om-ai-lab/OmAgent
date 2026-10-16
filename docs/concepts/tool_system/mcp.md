# Model Control Protocol (MCP)

OmAgent's Model Control Protocol (MCP) system enables seamless integration with external AI models and services through a standardized interface. This protocol allows OmAgent to dynamically discover, register, and execute tools from multiple external servers, extending its capabilities without modifying the core codebase.

## MCP Configuration File

MCP servers are configured in a JSON file, typically named `mcp.json`. This file defines the servers that OmAgent can connect to. Each server has a unique name, command to execute, arguments, and environment variables.

Here's an example of a basic `mcp.json` file that configures multiple MCP servers:

```json
{
  "mcpServers": {
    "desktop-commander": {
      "command": "npx",
      "args": [
        "-y",
        "@smithery/cli@latest",
        "run",
        "@wonderwhy-er/desktop-commander",
        "--key",
        "your-api-key-here"
      ]
    },
    .....
}
```

By default, OmAgent looks for this file in the following locations (in order):
1. Inside the tool_system directory `omagent-cor/src/omagnet_core/tool_system/mcp.json`
it will be automatically loaded.

## Executing MCP Tools

MCP tools can be executed just like any other tool using the ToolManager:

```python
# Let the ToolManager choose the appropriate tool
x = tool_manager.execute_task("command ls -l for the current directory")    
print (x)
```

For more details on creating MCP servers, refer to the [MCP specification](https://github.com/modelcontextprotocol/python-sdk).
