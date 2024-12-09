# AI Explainer Example

This example demonstrates how to use the framework for AI explainer tasks. The example code can be found in the `examples/ai_explainer` directory.

```bash
   cd examples/ai_explainer
```

## Overview

This example implements an intelligent explanation workflow that uses the switch-case functionality to achieve automatic determination of whether an input image is a landmark or a cultural relic, and explanation of the landmark or relic image, as well as relevant content recommendation. The workflow consists of the following key components:

1. **Input Interface**
   - Processes and caches a uploaded image

2. **Query Sight Or Artifact**
   - QuerySightOrArtifact: Analyzes whether the input image is a landmark or a cultural relic. If it is, processed with subsequent operations, otherwise, output 'The input image is neither a sight nor an artefact.'.

3. **Search Sight Or Artifact**
   - SearchSightOrArtifact: Only executes if QuerySightOrArtifact returns 1 (the input image is a landmark or a relic)
   - Uses web search functionality to retrieve up-to-date information on the landmark or relic

4. **generate_explanation**
   - Generates final explanation and relevant recommendation based on:
    - User's input image
    - Landmark or relic name
    - Retrieved information

The workflow follows this sequence:


## Prerequisites

- Python 3.10+
- Required packages installed (see requirements.txt)
- Access to OpenAI API or compatible endpoint (see configs/llms/gpt.yml)
- Access to Bing API key for web search functionality to search information for the up-to-date information on the landmark or relic (see configs/tools/websearch.yml)
- Redis server running locally or remotely
- Conductor server running locally or remotely

## Configuration

The container.yaml file is a configuration file that manages dependencies and settings for different components of the system, including Conductor connections, Redis connections, and other service configurations. To set up your configuration:

1. Generate the container.yaml file:
   ```bash
   python compile_container.py
   ```
   This will create a container.yaml file with default settings under `examples/ai_explainer`.



2. Configure your LLM settings in `configs/llms/gpt.yml` and `configs/llms/text_res.yml`:

   - Set your OpenAI API key or compatible endpoint through environment variable or by directly modifying the yml file
   ```bash
   export custom_openai_key="your_openai_api_key"
   export custom_openai_endpoint="your_openai_endpoint"
   ```
   - Configure other model settings like temperature as needed through environment variable or by directly modifying the yml file

3. Configure your Bing Search API key in `configs/tools/websearch.yml`:
   - Set your Bing API key through environment variable or by directly modifying the yml file
   ```bash
   export bing_api_key="your_bing_api_key"
   ```

4. Update settings in the generated `container.yaml`:
   - Modify Redis connection settings:
     - Set the host, port and credentials for your Redis instance
     - Configure both `redis_stream_client` and `redis_stm_client` sections
   - Update the Conductor server URL under conductor_config section
   - Adjust any other component settings as needed

## Running the Example

3. Run the outfit recommendation with switch example:

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

- Verify Conductor and Redis are running and accessible
- Check your OpenAI API key and Bing API key are valid
- Check Redis Stream client and Redis STM client configuration

- Ensure all dependencies are installed correctly
- Review logs for any error messages


## Building the Example

Coming soon! This section will provide detailed instructions for building the ai_explainer example step by step.

