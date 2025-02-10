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

<img src="../../docs/images/reflexion.png" width="400" alt="Reflexion Workflow">

### The workflow follows this pattern:
1. User provides input question
2. React Pro Loop:
   - Think about the question
   - Take an action
   - Search for information
   - Repeat until satisfied
3. Generate output and reflect
4. Either retry with new insights or finish
5. Provide final answer

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

You can run the example in three ways:

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

3. Running batch testing:
   ```bash
   python run_batch_test.py [options]
   ```

   Available options:
   ```bash
   --dataset       Dataset name (default: math500)
   --dataset_file  Path to dataset file (default: /path/to/math500.jsonl)
   ```

   Example usage:
   ```bash
   python run_batch_test.py --dataset custom_dataset --dataset_file data/custom_questions.jsonl
   ```

   The script will:
   - Read questions from the input dataset file
   - Process each question using the Reflexion workflow
   - Save results to `{dataset}_results.jsonl`

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
