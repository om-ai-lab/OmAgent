# Outfit Recommendation with Switch Example

This example demonstrates how to use the framework for outfit recommendation tasks with switch_case functionality. The example code can be found in the `examples/step2_outfit_with_switch` directory.

## Prerequisites

- Python 3.8+
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


2. Configure your LLM settings in `configs/llms/gpt.yml`:
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

3. Run the simple VQA example:

   For terminal/CLI usage:
   ```bash
   python run_cli.py
   ```

   For app/GUI usage:
   ```bash
   python run_app.py
   ```

## Example Usage

The system accepts two types of input:

1. Image Input:
   - Upload an image of your clothing item (e.g., a jacket, dress, or sweater)

2. Text Query:
   - After uploading the image, you can ask questions like:
     - "What should I pair this with for today's weather in New York?"
     - "I will go to work tommorrow morning, what should I wear?"
     - "Suggest a complete outfit suitable for my next meeting?"

The system will:
1. Analyze your uploaded clothing item
2. Search for real-time weather information for the specified location
3. Consider both the clothing item and weather conditions
4. Provide personalized outfit recommendations to complete your look

## Troubleshooting

If you encounter issues:
- Verify Redis is running and accessible
- Check your OpenAI API key is valid
- Ensure all dependencies are installed correctly
- Review logs for any error messages


## Building the Example

Coming soon! This section will provide detailed instructions for building the step2_outfit_with_switch example step by step.

