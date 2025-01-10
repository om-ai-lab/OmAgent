# Program of Thought (PoT) Example

Program of Thought (PoT) is a novel approach that combines language models with code execution to solve complex reasoning tasks. It leverages the model's ability to generate executable code that breaks down problems into computational steps, providing a more structured and verifiable solution path compared to traditional methods.

This example demonstrates how to use the framework for Program of Thought tasks. The example code can be found in the `examples/PoT` directory.

```bash
   cd examples/PoT
```

## Overview

This example implements a Program of Thought (PoT) workflow that consists of the following components:

1. **Input Interface**
   - Handles user input containing questions
   - Manages example prompts for few-shot learning
   - Processes additional options for the workflow

2. **PoT Workflow**
   - Takes the user's question and example prompts
   - Generates executable Python code to solve the problem
   - Executes the code to obtain numerical answers
   - Provides step-by-step reasoning through code

3. **PoT Executor**
   - Executes the generated Python code in a safe environment
   - Returns the computed answer

4. **Choice Extractor**
   - Compares the executed result with available choices
   - Returns the choice that most closely matches the result
   - Handles numerical and textual comparison to find best match

![DnC Workflow](./docs/images/pot_workflow.jpg)

## Prerequisites

- Python 3.10+
- Required packages installed (see requirements.txt)
- Access to OpenAI API or compatible endpoint (see configs/llms/gpt.yml)
- Redis server running locally or remotely
- Conductor server running locally or remotely

## Configuration

The container.yaml file is a configuration file that manages dependencies and settings for different components of the system, including Conductor connections, Redis connections, and other service configurations. To set up your configuration:

1. Generate the container.yaml file:
   ```bash
   python compile_container.py
   ```
   This will create a container.yaml file with default settings under `examples/PoT`.


2. Configure your LLM settings in `configs/llms/gpt.yml`:
   - Set your OpenAI API key or compatible endpoint through environment variable or by directly modifying the yml file
   ```bash
   export custom_openai_key="your_openai_api_key"
   export custom_openai_endpoint="your_openai_endpoint"
   export model_id="your_model_id"  # e.g. gpt-4, gpt-3.5-turbo
   ```
   - Configure other model settings like temperature as needed through environment variable or by directly modifying the yml file

3. Update settings in the generated `container.yaml`:
   - Modify Redis connection settings:
     - Set the host, port and credentials for your Redis instance
     - Configure `redis_stream_client` sections
   - Update the Conductor server URL under conductor_config section
   - Adjust any other component settings as needed

4. [Optional] Prepare example prompts:
   - Create a text file containing example math problems and their Python solutions
   - Use the format shown in eval_gsm8k_fewshot.py
   - Pass the file path using --examples when running evaluation

## Running the Example

3. Run the Program of Thought (PoT) example:

   For terminal/CLI usage:
   ```bash
   python run_cli.py
   ```

   For web interface usage:
   ```bash
   python run_webpage.py
   ```
   For evaluating on GSM8K dataset with few-shot examples:
   ```bash
   python eval_gsm8k_fewshot.py \
     --endpoint "https://api.openai.com/v1" \
     --api_key "your_openai_api_key" \
     --model_id "gpt-3.5-turbo" \
     --dataset_path "gsm8k_test.jsonl" \
     --examples "examples.txt" \  # Optional: provide custom examples
     --output_path "output"
   ```

   For evaluating on AQUA dataset with zero-shot learning:
   ```bash
   python eval_aqua_zeroshot.py \
     --endpoint "https://api.openai.com/v1" \
     --api_key "your_openai_api_key" \
     --model_id "gpt-3.5-turbo" \
     --dataset_path "aqua_test.jsonl" \
     --output_path "output"
   ```

   The evaluation scripts will:
   - Process questions from the dataset using Program of Thought approach
   - Generate Python code solutions for each question
   - Save results to JSON files in the specified output directory
   - Include metrics like prompt tokens and completion tokens


## Troubleshooting

If you encounter issues:
- Verify Redis is running and accessible
- Check your OpenAI API key is valid
- Ensure all dependencies are installed correctly
- Review logs for any error messages
- **Open an issue on GitHub if you can't find a solution, we will do our best to help you out!**
