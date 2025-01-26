# Video Understanding Example

This example demonstrates how to use the framework for hour-long video understanding task. The example code can be found in the `examples/video_understanding` directory.

```bash
   cd examples/video_understanding
```

## Overview

This example implements a video understanding task workflow based on the DnC workflow, which consists of following components:

1. **Video Preprocess Task**
   - Preprocess the video with audio information via speech-to-text capability
   - It detects the scene boundaries, splits the video into several chunks and extract frames at specified intervals
   - Each scene chunk is summarized by MLLM with detailed information, cached and updated into vector database for Q&A retrieval
   - Video metadata and video file md5 are transferred for filtering

2. **Video QA Task**
   - Take the user input question about the video
   - Retrieve related information from the vector database with the question
   - Extract the approximate start and end time of the video segment related to the question
   - Generate video object from serialized data in short-term memory(stm)
   - Build init task tree with the question to DnC task

3. **Divide and Conquer Task**
   - Execute the task tree with the question
   - Detailed information is referred to the [DnC Example](./DnC.md#overview)

The system uses Redis for state management, Milvus for long-tern memory storage and Conductor for workflow orchestration.

### This whole workflow is looked like the following diagram:

![Video Understanding Workflow](./docs/images/video_understanding_workflow_diagram.png)

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
   This will create a container.yaml file with default settings under `examples/video_understanding`.


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
   - The default text encoder configuration uses OpenAI `text-embedding-3-large` with **3072** dimensions, make sure you change the dim value of `MilvusLTM` in `container.yaml`
   - Configure other model settings like temperature as needed through environment variable or by directly modifying the yml file

3. Update settings in the generated `container.yaml`:
   - Modify Redis connection settings:
     - Set the host, port and credentials for your Redis instance
     - Configure both `redis_stream_client` and `redis_stm_client` sections
   - Update the Conductor server URL under conductor_config section
   - Configure MilvusLTM in `components` section:
     - Set the `storage_name` and `dim` for MilvusLTM
     - Set `dim` is to **3072** if you use default OpenAI encoder, make sure to modify corresponding dimension if you use other custom text encoder model or endpoint 
     - Adjust other settings as needed
   - Configure hyper-parameters for video preprocess task in `examples/video_understanding/configs/workers/video_preprocessor.yml`
     - `use_cache`: Whether to use cache for the video preprocess task
     - `scene_detect_threshold`: The threshold for scene detection, which is used to determine if a scene change occurs in the video, min value means more scenes will be detected, default value is **27**
     - `frame_extraction_interval`: The interval between frames to extract from the video, default value is **5**
     - `kernel_size`: The size of the kernel for scene detection, should be **odd** number, default value is automatically calculated based on the resolution of the video. For hour-long videos, it is recommended to leave it blank, but for short videos, it is recommended to set a smaller value, like **3**, **5** to make it more sensitive to the scene change
     - `stt.endpoint`: The endpoint for the speech-to-text service, default uses OpenAI ASR service
     - `stt.api_key`: The API key for the speech-to-text service, default uses OpenAI API key
   - Adjust any other component settings as needed

## Running the Example

1. Run the video understanding example via Webpage:

   ```bash
   python run_webpage.py
   ```

   First, select a video or upload a video file on the left; after the video preprocessing is completed, ask questions about the video content on the right.


2. Run the video understanding example, currently only supports CLI usage:

   ```bash
   python run_cli.py
   ```

   First time you need to input the video file path, it will take a while to preprocess the video and store the information into vector database.
   After the video is preprocessed, you can input your question about the video and the system will answer it. Note that the agent may give the wrong or vague answer, especially some questions are related the name of the characters in the video.

## Troubleshooting

If you encounter issues:
- Verify Redis is running and accessible
- Try smaller `scene_detect_threshold` and `frame_extraction_interval` if you find too many scenes are detected
- Check your OpenAI API key is valid
- Check your Bing API key is valid if search results are not as expected
- Check the `dim` value in `MilvusLTM` in `container.yaml` is set correctly, currently unmatched dimension setting will not raise error but lose partial of the information(we will add more checks in the future)
- Ensure all dependencies are installed correctly
- Review logs for any error messages
- **Open an issue on GitHub if you can't find a solution, we will do our best to help you out!**


4. Run the video understanding example, currently only supports Webpage usage:

   ```bash
   python run_webpage.py
   ```

   First, select a video or upload a video file on the left; after the video preprocessing is completed, ask questions about the video content on the right.
