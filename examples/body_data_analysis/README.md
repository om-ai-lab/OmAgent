# Body Data Analysis

This example shows how to implement body data based health analysis based on loop, sample code can be found in the `examples/body_data_analysis` directory.

```bash
   cd examples/body_data_analysis
```

## Overview

This example implements a body data analysis workflow that consists of the following key components:

1. **Body Data Acquisition**
Acquire and process user body data: the current user body data needs to be entered in advance in `examples/body_data_analysis/agent/body_data_acquisition/body_data.json`, the user can enter all the information, or only part of the information, the Agent will be based on the whether the information is missing or not and take the relevant query. (In the future, we will consider designing to get the relevant body data directly from the body fat scale)

2. **Interactive QA cycle**
   - BodyAnalysisQA: Conduct an interactive QA to gather additional information
   - Use web search tools to access specific BodyAnalysis content
   - BodyAnalysisDecider: assesses whether enough information is being collected based on the following factors
     - The user's physical condition
     - Physical health criteria
   - Use the DoWhileTask to continue the loop until enough information has been collected.
   - The loop terminates when BodyAnalysisDecider returns decision=true.

3. **Final analysis**
   - Body data analysis: Generate analysis based on
     - Information gathered in a question and answer cycle
     - Other information obtained through web searches

4. **Workflow Flow**
   ```
   Start -> Body Data Acquisition -> Body_analysis_qa_loop(QA + Weather Search + Decision) -> Final analysis -> End

   ```

Workflows utilize Redis for state management and the Conductor server for workflow orchestration. This architecture enables
- Acquisition of user body data
- Health advice using web data
- Interactive improvement through structured Q&A
- Context-aware recommendations that combine multiple factors
- Continuous state management throughout the workflow


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
   This will create a container.yaml file with default settings under `examples/body_data_analysis`.

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

1. Run the Body Data Analysis workflow:

   Before running you need to fill in the body data in `examples/body_data_analysis/agent/body_data_acquisition/body_data.json` to simulate the scale results (or not)
If you want to use Chinese prompt, you can change the suffix name of the prompt file in 'body_analysis_qa' and 'body_analysis_decider' to _zh, and set the language to 'zh' in the acquisition `body_data_string = get_body_data(body_data['Body_Data']. language = "zh")`

   For terminal/CLI usage:
   ```bash
   python run_cli.py
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
