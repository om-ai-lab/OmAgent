# ZoomEye Example

ZoomEye is an advanced visual search and analysis framework that combines visual understanding with search capabilities. It can pinpoint and identify visual elements by simulating human zoom-in image behavior through a tree-structured image analysis approach that interrogates image content in detail.

This example demonstrates how to use the OMAgent framework for visual search and analysis tasks. The example code can be found in the "examples/ZoomEye" directory.

```bash
cd examples/ZoomEye
```

## Overview

This example implements a comprehensive ZoomEye workflow that consists of the following components:

1. **ZoomEye Input**
   - Handles user input containing text queries and image uploads
   - Processes multi-modal inputs to prepare for visual analysis

2. **ZoomEye Workflow**
   - Builds a hierarchical image tree for multi-scale analysis
   - Performs confidence-guided search to locate visual elements
   - Uses adaptive thresholding to optimize search efficiency

### This workflow is structured as follows:

<img src="./doc/images/zoomeye_workflow.jpg" alt="ZoomEye Workflow" width="500" height="auto">

## Prerequisites

- Python 3.11+
- Required packages installed (see requirements.txt)
- Access to a multimodal LLM (e.g., LLaVA, GPT-4V) or compatible endpoint 
- Redis server running locally or remotely (for pro mode)
- Conductor server running locally or remotely (for pro mode)

## Configuration

The container.yaml file manages dependencies and settings for different components of the system. To set up your configuration:

1. Generate the container.yaml file:
   ```bash
   python compile_container.py
   ```
   This will create a container.yaml file with default settings under `examples/ZoomEye`.

2. Configure your multimodal LLM settings in `configs/llms/*.yml`:
   - Set your model endpoint through environment variables or by directly modifying the yml file
   ```bash
   export custom_openai_model_id="your_model_id"
   export custom_openai_key="your_openai_api_key"
   export custom_openai_endpoint="your_openai_endpoint"
   ```

   - Configure other model settings like temperature as needed

3. Update settings in the generated `container.yaml`:
   - Modify Redis connection settings (for pro mode):
     - Set the host, port and credentials for your Redis instance
     - Configure both `redis_stream_client` and `redis_stm_client` sections
   - Update the Conductor server URL under conductor_config section (for pro mode)
   - Adjust any other component settings as needed

## Running the Example

Run the ZoomEye example:

For terminal/CLI usage:
```bash
python run_cli.py
```

You can run the ZoomEye workflow in `pro` mode or `lite` mode by changing the `OMAGENT_MODE` environment variable. The default mode is `pro` which uses the conductor and redis server. The `lite` mode will run the workflow in the current python process without external services.

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

## How ZoomEye Works

ZoomEye uses a hierarchical approach to image analysis:

1. The image is first decomposed into a tree structure with multiple scales
2. Visual cues are extracted from the user's query to guide the search
3. A confidence-guided search algorithm traverses the image tree to locate visual elements
4. Adaptive thresholding ensures high-quality results while optimizing computation
5. Found elements are synthesized into a comprehensive answer

This approach enables precise localization of visual elements while maintaining computational efficiency.

## Troubleshooting

If you encounter issues:
- Verify your multimodal LLM endpoint is accessible and working
- For pro mode, confirm Redis is running and accessible
- Ensure all dependencies are installed correctly
- Check for sufficient GPU resources if using local model deployment
- Review logs for any error messages
- **Open an issue on GitHub if you can't find a solution, we will do our best to help you out!**

**Note**: 
1. The llm called by zoomeye needs to support the return of **logprobs**.
2. Sometimes you may encounter not enough memory error, because stm default size is 100MB, and when retrieve high definition image will be out of memory, if encountered, please adjust the function `_get_shm` in `omagent-core/src/omagent_core/memories/stms/stm_sharedMem.py` to get a larger size.
```python
92    def _get_shm(self, workflow_instance_id, size: int = 1024 * 1024 * 100):
...
103     return shm
```

