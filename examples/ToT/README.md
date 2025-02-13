# Tree-of-Thought Example

In computer science, "Tree of Thought" (ToT) is a tree-structured solution that maintains a tree of thoughts represented by a coherent sequence of language, which is the intermediate steps in solving the problem. Using this approach, LLM is able to evaluate the intermediate thoughts of a rigorous reasoning process. LLM combines the ability to generate and evaluate thoughts with search algorithms such as breadth-first search and depth-first search, which can verify forward and backward when systematically exploring thoughts.

This example demonstrates how to use the framework for a simple, ToT task. The example code can be found in the "examples/ToT" directory.

```bash
   cd examples/ToT
```

## Overview

This example implements a general ToT workflow that consists of following components:

1. **ToT Input**
   - Handles user input containing questions, requirements, and examples(if has)

2. **ToT Workflow**
   - Generate possible next thoughts
   - Evaluate the thoughts
   - Search the best thought

3. **ToT Output**
   - Output the last output in final result

### This whole workflow is looked like the following diagram:

![ToT Workflow](./docs/images/tot_run_structure.png)

## Prerequisites

- Python 3.11+
- Required packages installed (see requirements.txt)
- Access to OpenAI API or compatible endpoint (see configs/llms/*.yml)
- Redis server running locally or remotely
- Conductor server running locally or remotely

## Configuration

The container.yaml file is a configuration file that manages dependencies and settings for different components of the system, including Conductor connections, Redis connections, and other service configurations. To set up your configuration:

1. Generate the container.yaml file:
   ```bash
   python compile_container.py
   ```
   This will create a container.yaml file with default settings under `examples/ToT`.


2. Configure your LLM and tool settings in `configs/llms/*.yml` and `configs/tools/*.yml`:
   - Set your OpenAI API key or compatible endpoint through environment variable or by directly modifying the yml file
   ```bash
   export custom_model_id="your_model_id"
   export custom_openai_key="your_openai_api_key"
   export custom_openai_endpoint="your_openai_endpoint"
   ```

   - Configure other model settings like temperature as needed through environment variable or by directly modifying the yml file

3. Update settings in the generated `container.yaml`:
   - Modify Redis connection settings:
     - Set the host, port and credentials for your Redis instance
     - Configure both `redis_stream_client` and `redis_stm_client` sections
   - Update the Conductor server URL under conductor_config section
   - Adjust any other component settings as needed

## Running the Example

3. Run the general ToT example:

   For terminal/CLI usage:
   ```bash
   python run_cli.py
   ```

   You can now run the ToT workflow in `pro` mode or `lite` mode by changing the `OMAGENT_MODE` environment variable. The default mode is `pro` which use the conductor and redis server to run the workflow. The `lite` mode will run the workflow in the current python process without using the conductor and redis server.

   For pro mode:
   ```bash
   export OMAGENT_MODE="pro"
   python run_cli.py
   ```

   For lite mode:
   ```bash
   export OMAGENT_MODE="lite"
   python run_cli.py
   ```



## Troubleshooting

If you encounter issues:
- Verify Redis is running and accessible
- Check your OpenAI API key is valid
- Check your Bing API key is valid if search results are not as expected
- Ensure all dependencies are installed correctly
- Review logs for any error messages
- **Open an issue on GitHub if you can't find a solution, we will do our best to help you out!**


## Set up your own ToT workflow

ToT has many other complex settings. If you want to learn more about ToT settings, please follow this document.[ToT User Book](./docs/files/user_book.md)