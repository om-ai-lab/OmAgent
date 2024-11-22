# Divide-and-Conquer Example

In computer science, divide and conquer is an algorithm design paradigm. A divide-and-conquer algorithm recursively breaks down a problem into two or more sub-problems of the same or related type, until these become simple enough to be solved directly. The solutions to the sub-problems are then combined to give a solution to the original problem.

This example demonstrates how to use the framework for divide-and-conquer tasks. The example code can be found in the `examples/general_dnc` directory.

```bash
   cd examples/general_dnc
```

## Overview

This example implements a general divide-and-conquer workflow that consists of following components:

1. **DnC Input Interface**
   - Handles user input containing questions and(or) images
   - Construct data structure for workflow running

2. **Init Set Variable Task**
   - Initialize global workflow variables that is needed in the entire workflow
  
3. **Conqueror Task**
   - Conqueror task executes and manages complex task trees: direct agent answer, conquer current task, use tool call for current task or break current task into several subtasks
   - It takes a hierarchical task tree and processes each task node, maintaining context and state between task executions

4. **Conqueror Update Set Variable Task**
   - Update global workflow variables changed after conqueror task excution for better reading experience in conductor UI
  
5. **Divider Task**
   - Break down complex task into multiple smaller subtasks
   - Generate and match milestones to each subtask

6. **Divider Update Set Variable Task**
   - Update global workflow variables changed after divider task excution for better reading experience in conductor UI

7. **Rescue Task**
   - Rescue failed tool call task, attempt to fix the issue by retrying with corrected parameters

8. **Conclude Task**
   - Solid end of the workflow, conclude the original root task based on all related information

9.  **Switch Task**
    - After conqueror task, based on it's dicision, switch to specific next worker.
    - Default case is the next conqueror task
    - If too complex, switch to divider task
    - If failed, switch to rescue task

10. **Task Exit Monitor Task**
    - Monitor whether the exit condition of the DnC loop task is met
    - Based on the conqueror and divider task(s), the task tree is dynamicly generated and continuesly updated in the whole workflow

11. **Post Set Variable Task**
    - Update global workflow variables changed after task exit monitor task execution for better reading experience in conductor UI

12. **DnC Loop Task**
    - The core of the DnC workflow, takes a hierarchical task tree and processes each task node, maintaining context and state between task executions
    - It contains three main tasks: conqueror task, divider task and rescue task, and other supporting tasks mentioned above

### This whole workflow is looked like the following diagram:

![DnC Workflow](../images/general_dnc_workflow_diagram.png)

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

