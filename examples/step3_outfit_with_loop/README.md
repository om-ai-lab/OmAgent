# Outfit Recommendation with Loop Example

This example demonstrates how to use the framework for outfit recommendation tasks with loop functionality. The example code can be found in the `examples/step3_outfit_with_loop` directory.
```bash
   cd examples/step3_outfit_with_loop
```

## Overview

This example implements an interactive outfit recommendation workflow that uses a loop-based approach to refine recommendations based on user feedback. The workflow consists of the following key components:

1. **Initial Image Input**
   - OutfitImageInput: Handles the upload and processing of the initial clothing item image
   - Serves as the starting point for the recommendation process

2. **Interactive QA Loop with Weather Integration**
   - OutfitQA: Conducts an interactive Q&A session to gather context and preferences
   - Uses web search tool to fetch real-time weather data for the specified location
   - OutfitDecider: Evaluates if sufficient information has been collected based on:
     - User preferences
     - Current weather conditions
   - Uses DoWhileTask to continue the loop until adequate information is gathered
   - Loop terminates when OutfitDecider returns decision=true

3. **Final Recommendation**
   - OutfitRecommendation: Generates the final outfit suggestions based on:
     - The initial uploaded image
     - Information collected during the Q&A loop
     - Current weather conditions from web search
     - Other context (occasion, preferences, etc.)

4. **Workflow Flow**
   ```
   Start -> Image Input -> OutfitQA Loop (QA + Weather Search + Decision) -> Final Recommendation -> End
   ```

The workflow leverages Redis for state management and the Conductor server for workflow orchestration. This architecture enables:
- Image-based outfit recommendations
- Weather-aware outfit suggestions using real-time data
- Interactive refinement through structured Q&A
- Context-aware suggestions incorporating multiple factors
- Persistent state management across the workflow


## Prerequisites

- Python 3.10+
- Required packages installed (see requirements.txt)
- Access to OpenAI API or compatible endpoint
- Access to Bing API key for web search functionality to search real-time weather information for outfit recommendations (see configs/tools/websearch.yml)
- Redis server running locally or remotely
- Conductor server running locally or remotely

## Configuration

The container.yaml file is a configuration file that manages dependencies and settings for different components of the system, including Conductor connections, Redis connections, and other service configurations. To set up your configuration:

1. Generate the container.yaml file:
   ```bash
   python compile_container.py
   ```
   This will create a container.yaml file with default settings under `examples/step3_outfit_with_loop`.

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

1. Run the outfit recommendation workflow:

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
- Check your OpenAI API key and Bing API key are valid
- Ensure all dependencies are installed correctly
- Review logs for any error messages
- Confirm Conductor server is running and accessible
- Check Redis Stream client and Redis STM client configuration

## Building the Example

Coming soon! This section will provide detailed instructions for building the step3_outfit_with_loop example step by step.
