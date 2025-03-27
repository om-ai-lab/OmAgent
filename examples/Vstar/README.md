# VStar Example

VStar is a workflow that utilizes visual contextual information to process high-definition images. It utilizes hierarchical image structures and adaptive thresholding to efficiently identify objects relevant to user queries.

This example demonstrates how to use the OMAgent framework for visual search and analysis tasks. The example code can be found in the "examples/VStar" directory.

```bash
cd examples/VStar
```

## Overview

This example implements a comprehensive VStar workflow that consists of the following components:

1. **VStar Input**
   - Handles user input containing text queries and image uploads
   - Processes multi-modal inputs to prepare for visual analysis

2. **Vstar Workflow**
   - Determine the elements needed to answer the question
   - Performing confidence-guided searches to localize visual elements
   - Optimize search efficiency using adaptive thresholding

### This workflow is structured as follows:

<img src="./docs/images/vstar_workflow.jpg" alt="VStar Workflow" width="500" height="auto">

## Prerequisites

- Python 3.11+
- Required packages installed (see requirements.txt)
- Access to a multimodal LLM (e.g., LLaVA, GPT-4V) or compatible endpoint 
- Redis server running locally or remotely (for pro mode)
- Conductor server running locally or remotely (for pro mode)

## Configuration

The `container.yaml` file manages dependencies and settings for different components of the system. To set up your configuration:

1. Generate the `container.yaml` file:
   ```bash
   python compile_container.py
   ```
   This will create a `container.yaml` file with default settings under `examples/VStar`.

2. Configure your multimodal LLM settings in `configs/llms/*.yml`:
   - Set your model endpoint through environment variables or by directly modifying the yml file
   ```bash
   export custom_vstar_endpoint="your_vstar_endpoint"
   ```

   - Configure other model settings like temperature as needed.

3. Update settings in the generated `container.yaml`:
   - Modify Redis connection settings (for pro mode):
     - Set the host, port, and credentials for your Redis instance.
     - Configure both `redis_stream_client` and `redis_stm_client` sections.
   - Update the Conductor server URL under the conductor_config section (for pro mode).
   - Adjust any other component settings as needed.

## Running the Example

Run the VStar example:

For terminal/CLI usage:
```bash
python run_cli.py
```

You can run the VStar workflow in `pro` mode or `lite` mode by changing the `OMAGENT_MODE` environment variable. The default mode is `pro`, which uses the conductor and Redis server. The `lite` mode will run the workflow in the current Python process without external services.

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

## How VStar Works

VStar uses a hierarchical approach to image analysis:

1. The image is first processed to extract relevant features and prepare for analysis.
2. Visual cues are generated from the user's query to guide the search.
3. A confidence-guided search algorithm traverses the image data to locate visual elements.
4. Adaptive thresholding ensures high-quality results while optimizing computation.
5. Found elements are synthesized into a comprehensive answer.

This approach enables precise localization of visual elements while maintaining computational efficiency.

## Troubleshooting

If you encounter issues:
- Verify your multimodal LLM endpoint is accessible and working.
- For pro mode, confirm Redis is running and accessible.
- Ensure all dependencies are installed correctly.
- Check for sufficient GPU resources if using local model deployment.
- Review logs for any error messages.
- **Open an issue on GitHub if you can't find a solution; we will do our best to help you out!**

## Local deployment of vstar

Since vstar does not yet support deployment by vllm, for example, we need to deploy locally.
First of all, go to V*'s code repository and download the [source code](https://github.com/penghao-wu/vstar)
, then copy the python file `OmAgent/examples/Vstar/docs/files/vstar_api.py` for deploying the api to the vstar source folder, and change the model path to your download seal models. Finally run `uvicorn vstar_api:app --host 0.0.0.0 --port 8000` to start the service, and then `export custom_vstar_endpoint=http://localhost:8000/`.