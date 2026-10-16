# ReAct Pro Example

ReAct Pro (Reasoning and Acting) is an enhanced version of the ReAct paradigm that separates the thinking and acting steps for better control and observation. The agent uses a three-step process: Think (reasoning), Act (determining action), and Observe (processing results).

This example demonstrates how to use the framework for ReAct Pro tasks. The example code can be found in the `examples/react_pro` directory.

```bash
cd examples/react_pro
```

## Overview

This example implements a ReAct Pro workflow that consists of following components:

1. **Input Interface**
   - Handles user input containing questions
   - Supports both CLI and programmatic interfaces

2. **ReAct Pro Workflow**
   - Think: Reason about the current state
   - Act: Decide the next action
   - Observe: Process the results of the action
   - Repeat until the task is complete or max steps reached

### The workflow follows this pattern:

<img src="../../docs/images/react_pro.png" width="200" alt="ReAct Pro Workflow">

1. User provides input (question)
2. Agent thinks about the question
3. Agent decides on an action
4. Agent observes the result
5. Process repeats until the answer is found

## Prerequisites

- Python 3.10+
- Required packages installed (see requirements.txt)
- Access to OpenAI API or compatible endpoint (see configs/llms/*.yml)
- Redis server running locally or remotely
- Conductor server running locally or remotely

## Configuration

The container.yaml file manages dependencies and settings for different components of the system. To set up your configuration:

1. Configure your container.yaml:
   - Set Redis connection settings for both `redis_stream_client` and `redis_stm_client`
   - Update the Conductor server URL under conductor_config section
   - Adjust any other component settings as needed

2. Configure your LLM settings in configs:
   ```bash
   export custom_openai_key="your_openai_api_key"
   export custom_openai_endpoint="your_openai_endpoint"
   ```

## Running the Example

You can run the example in two modes:

### Lite Mode (Local Execution)
Set the environment variable before running:
```bash
export OMAGENT_MODE="lite"
```
This mode runs the workflow locally without requiring a Conductor server.

### Conductor Mode (Distributed Execution)
Set the environment variable (or don't set it, as this is the default):
```bash
export OMAGENT_MODE="conductor"  # or just don't set OMAGENT_MODE
```
This mode requires a running Conductor server for workflow orchestration.

You can run the example in three ways:

1. Using the CLI interface:
   ```bash
   python run_cli.py
   ```

2. Using the programmatic interface:
   ```bash
   python run_programmatic.py
   ```

3. Running batch testing with dataset:
   ```bash
   python run_batch_test.py [options]
   ```
   This script will:
   - Read questions from the input dataset
   - Process each question using the ReAct Pro workflow
   - Save the results in a standardized format
   - Output results to `data/{dataset_name}_{alg}_{model_id}_results.json`

   Available options:
   ```bash
   --input_file     Input dataset file path (relative to project root)
                    Default: data/hotpot_dev_select_500_data_test_0107.jsonl
   
   --dataset_name   Name of the dataset
                    Default: hotpot
   
   --model_id       Model identifier
                    Default: gpt-3.5-turbo
   
   --alg           Algorithm name
                    Default: ReAct-Pro
   
   --output_dir    Output directory for results (relative to project root)
                    Default: data
   ```

   Example usage:
   ```bash
   python run_batch_test.py \
       --input_file data/custom_test.jsonl \
       --dataset_name custom \
       --model_id gpt-4 \
       --alg ReAct-Pro-v2 \
       --output_dir results
   ```

When running the CLI or programmatic interface, you'll be prompted to input your question.

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

Here's a simple example of using the ReAct Pro agent:

```bash
$ python run_cli.py

Please input your question:
When was Albert Einstein born?

[Agent starts reasoning and acting...]
```

The agent will then:
1. Think about how to answer the question
2. Decide on an appropriate action
3. Process the action results
4. Provide a final answer based on the found information 