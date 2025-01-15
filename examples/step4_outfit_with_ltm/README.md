# Outfit Recommendation with Long-Term Memory Example

This example demonstrates how to use the framework for outfit recommendation tasks with long-term memory functionality. The example code can be found in the `examples/step4_outfit_with_ltm` directory.
```bash
   cd examples/step4_outfit_with_ltm
```


## Overview

This example implements an outfit recommendation system with long-term memory capabilities through two main workflows:

1. **Image Storage Workflow**
   - ImageIndexListener: Monitors and captures new clothing images
   - OutfitImagePreprocessor: Processes and prepares images for storage
   - Stores processed images in Milvus long-term memory (LTM) for future retrieval
   - Workflow sequence: Image Listening -> Preprocessing -> LTM Storage

2. **Outfit Recommendation Workflow**
   - OutfitQA: Conducts interactive Q&A to understand user preferences
   - OutfitDecider: Determines if sufficient information is collected
   - Uses DoWhileTask for iterative refinement until decision is positive
   - OutfitGeneration: Generates outfit recommendations using stored image data
   - OutfitConclusion: Presents final recommendations with explanations

The system leverages both short-term memory (Redis STM) and long-term memory (Milvus LTM) for:
- Efficient image storage and retrieval
- Persistent clothing item database
- Context-aware outfit recommendations
- Interactive preference refinement
- Stateful conversation management

3. **Workflow Architecture**
   ```
   Image Storage:    Listen -> Preprocess -> Store in LTM
   Recommendation:   QA Loop (QA + Decision) -> Generation -> Conclusion
   ```

The system uses Redis for state management, Milvus for long-term image storage, and Conductor for workflow orchestration. This architecture enables:
- Scalable image database management
- Intelligent outfit recommendations based on stored items
- Interactive preference gathering
- Persistent clothing knowledge base
- Efficient retrieval of relevant items

## Prerequisites

- Python 3.10+
- Required packages installed (see requirements.txt)
- Access to OpenAI API or compatible endpoint (see configs/llms/gpt.yml)
- Access to Bing API key for web search functionality to search real-time weather information for outfit recommendations (see configs/tools/websearch.yml)
- Redis server running locally or remotely
- Conductor server running locally or remotely
- Milvus vector database (will be started automatically when workflow runs)
- Sufficient storage space for image database
- Install Git LFS by `git lfs intall`, then pull sample images by `git lfs pull`

## Configuration

The container.yaml file is a configuration file that manages dependencies and settings for different components of the system, including Conductor connections, Redis connections, Milvus connections and other service configurations. To set up your configuration:

1. Generate the container.yaml files:
   ```bash
   # For image storage workflow
   python image_storage/compile_container.py
   
   # For outfit recommendation workflow
   python outfit_from_storage/compile_container.py
   ```
   This will create two container.yaml files with default settings under `image_storage` and `outfit_from_storage` directories:
   - `image_storage/container.yaml`: Configuration for the image storage workflow
   - `outfit_from_storage/container.yaml`: Configuration for the outfit recommendation workflow

2. Configure your LLM settings in `configs/llms/gpt.yml` and `configs/llms/text_res.yml` in the two workflow directories:
   - Set your OpenAI API key or compatible endpoint through environment variable or by directly modifying the yml file
   ```bash
   export custom_openai_key="your_openai_api_key"
   export custom_openai_endpoint="your_openai_endpoint"
   ```
   - Configure other model settings like temperature as needed through environment variable or by directly modifying the yml file

3. Configure your Bing Search API key in `configs/tools/websearch.yml` in the two workflow directories:
   - Set your Bing API key through environment variable or by directly modifying the yml file
   ```bash
   export bing_api_key="your_bing_api_key"
   ```
4. Configure your text encoder settings in `configs/llms/text_encoder.yml` in the two workflow directories:
   - Set your OpenAI text encoder endpoint and API key through environment variable or  by directly modifying the yml file
   ```bash
   export custom_openai_text_encoder_key="openai_text_encoder_key"
   export custom_openai_text_encoder_endpoint="your_openai_endpoint"
   ```
   - The default text encoder configuration uses OpenAI text embedding v3 with 3072 dimensions, make sure you change the dim value of `MilvusLTM` in `container.yaml`
   - Adjust the embedding dimension and other settings as needed through environment variable or by directly modifying the yml file

4. Update settings in the generated `container.yaml`:
   - Modify Redis connection settings:
     - Set the host, port and credentials for your Redis instance
     - Configure both `redis_stream_client` and `redis_stm_client` sections
   - Update the Conductor server URL under conductor_config section
   - Configure MilvusLTM in `components` section:
     - Set the `storage_name` and `dim` for MilvusLTM
     - Adjust other settings as needed
   - Adjust any other component settings as needed

## Running the Example

1. Run the image storage workflow first:

   For terminal/CLI usage:
   ```bash
   python image_storage/run_image_storage_cli.py
   ```
   For app usage:
   ```bash
   python image_storage/run_image_storage_app.py
   ```

   This workflow will store outfit images in the Milvus database.

2. Run the outfit recommendation workflow in a separate terminal:

   For terminal/CLI usage:
   ```bash
   python outfit_from_storage/run_outfit_recommendation_cli.py
   ```

   For app/GUI usage:
   ```bash
   python outfit_from_storage/run_outfit_recommendation_app.py
   ```

   This workflow will retrieve outfit recommendations from the stored images.


## Troubleshooting

If you encounter issues:
- Verify Redis is running and accessible
- Check your OpenAI API key and Bing API key are valid
- Ensure all dependencies are installed correctly
- Review logs for any error messages
- Confirm Conductor server is running and accessible
- Check Redis Stream client and Redis STM client configuration

## Building the Example

Coming soon! This section will provide detailed instructions for building the step4_outfit_with_ltm example step by step.
    
