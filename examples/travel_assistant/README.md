# Travel Recommendation with Loop Example

This example demonstrates how to use the framework for travel assistance tasks with loop functionality. The example code can be found in the `examples/travel_assistant` directory.
```bash
   cd examples/travel_assistant
```

## Overview

This example implements an interactive travel assistant workflow that uses a loop-based approach to refine recommendations based on user feedback. The workflow consists of the following key components:

1. **Initial Travel Details Input**
   - DestinationInput: Handles the input and processing of initial travel details such as destination, dates, and preferences
   - Serves as the starting point for the travel planning process

2. **Interactive QA Loop with Preferences Integration**
   - ScenicSpotQA: Conducts an interactive Q&A session to gather context and preferences
   - Uses web search tool to fetch real-time weather data for the specified location
   - ScenicSpotDecider: Evaluates if sufficient information has been collected based on:
     - User preferences
     - Real-time destination information
   - Uses DoWhileTask to continue the loop until adequate information is gathered
   - Loop terminates when ScenicSpotDecider returns decision=true

3. **Final Scenic Spot Recommendation**
   - ScenicSpotRecommendation: Generates the final scenic spot suggestions based on:
     - The initial input details
     - Information collected during the Q&A loop
     - Real-time destination information from web search
     - Other context (preferences, special requirements, etc.)

4. **Workflow Flow**
   ```
   Start -> Initial Travel Details Input -> ScenicSpotQA Loop (QA + Destination Info + Decision) -> Final Scenic Spot Recommendation -> End
   ```

The workflow leverages Redis for state management and the Conductor server for workflow orchestration. This architecture enables:
- Scenice spot recommendations
- Weather-aware outfit suggestions using real-time data
- Interactive refinement through structured Q&A
- Context-aware suggestions incorporating multiple factors
- Persistent state management across the workflow


## Prerequisites

- Python 3.10+
- Required packages installed (see requirements.txt)
- Access to OpenAI API or compatible endpoint
- Access to Bing API key for web search functionality to search real-time weather information for scenic spot recommendations (see configs/tools/all_tools.yml)
- Redis server running locally or remotely
- Conductor server running locally or remotely

## Configuration

The container.yaml file is a configuration file that manages dependencies and settings for different components of the system, including Conductor connections, Redis connections, and other service configurations. To set up your configuration:

1. Generate the container.yaml file:
   ```bash
   python compile_container.py
   ```
   This will create a container.yaml file with default settings under `examples/travel_assistant`.

2. Configure your LLM settings in `configs/llms/gpt.yml` and `configs/llms/text_res.yml`:
   - Set your OpenAI API key or compatible endpoint through environment variable or by directly modifying the yml file
   ```bash
   export custom_openai_key="your_openai_api_key"
   export custom_openai_endpoint="your_openai_endpoint"
   ```
   - Configure other model settings like temperature as needed through environment variable or by directly modifying the yml file

3. Configure your Bing Search API key in `configs/tools/all_tools.yml`:
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

1. Run the scenic spot recommendation workflow:

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

