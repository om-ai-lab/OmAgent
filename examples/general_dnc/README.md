# Divide-and-Conquer Example

In computer science, divide and conquer is an algorithm design paradigm. A divide-and-conquer algorithm recursively breaks down a problem into two or more sub-problems of the same or related type, until these become simple enough to be solved directly. The solutions to the sub-problems are then combined to give a solution to the original problem.

This example demonstrates how to use the framework for divide-and-conquer tasks. The example code can be found in the `examples/general_dnc` directory.

```bash
   cd examples/general_dnc
```

## Overview

This example implements a general divide-and-conquer workflow that consists of following components:

1. **Input Interface**
   - Handles user input containing questions and(or) images

2. **DnC Workflow**
   - Decompose the original task into multiple sub-tasks
   - Conquer each sub-task to complete the original task

3. **Conclude Task**
   - Solid end of the workflow, conclude the original root task based on all related information

### This whole workflow is looked like the following diagram:

![DnC Workflow](./docs/images/general_dnc_workflow_diagram.png)

## Prerequisites

- Python 3.10+
- Required packages installed (see requirements.txt)
- Access to OpenAI API or compatible endpoint (see configs/llms/*.yml)
- [Optional] Access to Bing API for WebSearch tool (see configs/tools/*.yml)
- Redis server running locally or remotely
- Conductor server running locally or remotely

## Configuration

The container.yaml file is a configuration file that manages dependencies and settings for different components of the system, including Conductor connections, Redis connections, and other service configurations. To set up your configuration:

1. Generate the container.yaml file:
   ```bash
   python compile_container.py
   ```
   This will create a container.yaml file with default settings under `examples/general_dnc`.


2. Configure your LLM and tool settings in `configs/llms/*.yml` and `configs/tools/*.yml`:
   - Set your OpenAI API key or compatible endpoint through environment variable or by directly modifying the yml file
   ```bash
   export custom_openai_key="your_openai_api_key"
   export custom_openai_endpoint="your_openai_endpoint"
   ```
   - [Optional] Set your Bing API key or compatible endpoint through environment variable or by directly modifying the yml file
   ```bash
   export bing_api_key="your_bing_api_key"
   ```
   **Note: It isn't mandatory to set the Bing API key, as the WebSearch tool will rollback to use duckduckgo search. But it is recommended to set it for better search quality.**
   - Configure other model settings like temperature as needed through environment variable or by directly modifying the yml file

3. Update settings in the generated `container.yaml`:
   - Modify Redis connection settings:
     - Set the host, port and credentials for your Redis instance
     - Configure both `redis_stream_client` and `redis_stm_client` sections
   - Update the Conductor server URL under conductor_config section
   - Adjust any other component settings as needed

## Running the Example

3. Run the general DnC example:

   For terminal/CLI usage:
   ```bash
   python run_cli.py
   ```

   For app/GUI usage:
   ```bash
   python run_app.py
   ```

## Troubleshooting

If you encounter issues:
- Verify Redis is running and accessible
- Check your OpenAI API key is valid
- Check your Bing API key is valid if search results are not as expected
- Ensure all dependencies are installed correctly
- Review logs for any error messages
- **Open an issue on GitHub if you can't find a solution, we will do our best to help you out!**


## Building the Example

Coming soon! This section will provide detailed instructions for building and packaging the general_dnc example step by step.

