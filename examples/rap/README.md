# Reasoning via Planning (RAP) Example

This example demonstrates how to use the RAP (Reasoning via Planning) operator for complex reasoning tasks. The RAP operator treats reasoning as a planning problem and uses Monte Carlo Tree Search (MCTS) to explore reasoning paths.

> **Note**: RAP currently only supports the lite version because Conductor cannot handle nested loops (loops inside loops) which are required for the MCTS algorithm.

## Overview

The example implements a RAP workflow with three main components:

1. **Input Interface**
   - Handles user input for math problems
   - Provides a simple CLI interface

2. **RAP Workflow**
   - Uses MCTS to explore reasoning paths
   - Leverages a language model for reasoning
   - Finds optimal solution paths

3. **Conclude Task**
   - Extracts and formats the final answer
   - Presents results to the user

## Prerequisites

- Access to OpenAI API or compatible endpoint

## Setup

Configure environment variables:
```bash
export custom_openai_key="your_openai_api_key"
export custom_openai_endpoint="your_openai_endpoint"  # Optional: defaults to https://api.openai.com/v1
```

## Running the Example

Only the lightweight version is supported:
```bash
python run_cli_lite.py
```

The CLI will prompt you to:
1. Select a task type (currently supports 'math')
2. Enter your problem/question

## Configuration Files

- `configs/llms/gpt.yml`: LLM settings
  ```yaml
  name: OpenaiGPTLLM
  model_id: gpt-4o-mini
  api_key: ${env| custom_openai_key}
  endpoint: ${env| custom_openai_endpoint, https://api.openai.com/v1}
  temperature: 0.0
  vision: false
  ```

- `configs/workers/rap_workflow.yml`: Worker configurations for the RAP pipeline

## Example Usage in Code

```python
from omagent_core.advanced_components.workflow.rap import RAPWorkflow

# Initialize RAP workflow
workflow = RAPWorkflow()

# Set input query
workflow.set_input(query="If 4 friends share 7 pizzas equally, and each pizza has 8 slices, how many slices does each friend get?")

# Get results
final_answer = workflow.final_answer
```

## Troubleshooting

Common issues:
- Invalid API key: Verify your OpenAI API key is set correctly
- Connection errors: Check your internet connection and API endpoint
- Import errors: Ensure all dependencies are installed

For more detailed documentation, visit the [OmAgent documentation](https://docs.omagent.ai).
