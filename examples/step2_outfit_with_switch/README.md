# Outfit Recommendation with Switch Example

This example demonstrates how to use the framework for outfit recommendation tasks with switch_case functionality. The example code can be found in the `examples/step2_outfit_with_switch` directory.

```bash
   cd examples/step2_outfit_with_switch
```

## Overview

This example implements an outfit recommendation workflow that uses switch-case functionality to conditionally include weather information in the recommendation process. The workflow consists of the following key components:

1. **Input Interface**
   - Handles user input containing clothing requests and image data
   - Processes and caches any uploaded images
   - Extracts the user's outfit request instructions

2. **Weather Decision Logic**
   - WeatherDecider: Analyzes the user's request to determine if weather information is needed
   - Makes a binary decision (0 or 1) based on context in the user's request
   - Controls whether weather data should be fetched

3. **Conditional Weather Search**
   - WeatherSearcher: Only executes if WeatherDecider returns 0 (weather info needed)
   - Uses web search functionality to fetch current weather conditions
   - Integrates weather data into the recommendation context

4. **Outfit Recommendation**
   - Generates final clothing suggestions based on:
     - User's original request
     - Weather information (if available)
     - Any provided image context
   - Provides complete outfit recommendations

The workflow follows this sequence:


## Prerequisites

- Python 3.10+
- Required packages installed (see requirements.txt)
- Access to OpenAI API or compatible endpoint (see configs/llms/gpt.yml)
- Access to Bing API key for web search functionality to search real-time weather information for outfit recommendations (see configs/tools/websearch.yml)
- Redis server running locally or remotely
- Conductor server running locally or remotely

## Configuration

The container.yaml file is a configuration file that manages dependencies and settings for different components of the system, including Conductor connections, Redis connections, and other service configurations. To set up your configuration:

1. Generate the container.yaml file:
   ```bash
   python compile_container.py
   ```
   This will create a container.yaml file with default settings under `examples/step2_outfit_with_switch`.



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

Coming soon! This section will provide detailed instructions for building the step2_outfit_with_switch example step by step.

