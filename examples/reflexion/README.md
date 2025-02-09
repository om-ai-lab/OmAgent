# Reflexion Example

Reflexion is an enhanced reasoning framework that achieves continuous improvement through self-reflection. The core mechanism includes an iterative process of reasoning, execution, evaluation, and reflection. This example demonstrates how to implement the Reflexion pattern in the framework. The example code can be found in the `examples/reflexion` directory.

```bash
cd examples/reflexion
```

## Overview

This example implements a Reflexion workflow that consists of following components:

1. **Reflection Engine**
   - Maintains iteration state machine
   - Executes self-evaluation checkpoints
   - Generates improvement strategies

2. **Multi-stage Workflow**
   ```mermaid
   graph TD
   A[Initial Reasoning] --> B[Execute Action]
   B --> C{Evaluate Results}
   C -->|Pass| D[Output Answer]
   C -->|Fail| E[Generate Reflection]
   E --> F[Update Knowledge]
   F --> A
   ```

### The workflow follows this pattern:
1. User provides input (question)
2. Generate initial reasoning chain
3. Execute actions and observe results
4. Evaluate result quality
5. Generate reflection if not satisfactory
6. Update knowledge base based on reflection
7. Repeat until termination conditions are met

## Prerequisites

- Python 3.10+
- Required packages installed (see requirements.txt)
- Supported LLM services:
  - OpenAI API
  - Azure OpenAI
  - Compatible local endpoints
- Redis 5.0+ for memory database
- Conductor for task scheduling

## Configuration

Configure your LLM settings in configs:
```bash
export custom_openai_key="your_openai_api_key"
export custom_openai_endpoint="your_openai_endpoint"
```

## Running the Example

You can run the example in two ways:

1. Using the CLI interface:
   ```bash
   python reflect_cli.py
   ```

2. Using the programmatic interface:
   ```python
   from reflexion_agent import ReflexionAgent

   agent = ReflexionAgent.from_config("configs/default.yml")
   result = agent.solve("In which year did Einstein receive the Nobel Prize?")
   ```

## Troubleshooting

If you encounter issues:
- Verify Redis is running and accessible
- Check your OpenAI API key is valid
- Ensure all dependencies are installed correctly
- Review logs for any error messages
- Check the proxy settings if needed

Common issues:
- Connection errors: Check your network settings
- LLM errors: Verify your API key and endpoint
- Redis errors: Ensure Redis server is running

## Example Usage

Here's a simple example of using the Reflexion agent:

```bash
$ python reflect_cli.py

Please input your question:
In which year did Einstein receive the Nobel Prize?

[Agent starts reasoning and reflecting...]
```

The agent will then:
1. Generate initial reasoning
2. Execute and evaluate the result
3. Reflect and improve if needed
4. Provide a final answer based on the reflection process
