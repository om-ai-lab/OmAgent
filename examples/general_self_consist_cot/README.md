# SELF-CONSISTENCY IMPROVES CHAIN OF THOUGHT REASONING IN LANGUAGE MODELS

## Overview

This example contains code to implement the self-consistency COT in the paper [SELF-CONSISTENCY IMPROVES CHAIN OF THOUGHT REASONING IN LANGUAGE MODELS](https://arxiv.org/pdf/2203.11171) by Wang, et al. 
Please note:
The algorithm in original paper is designed only for math reasoning, the implementation here is for general reasoning.

### Algorithm Overview
<div align="center">
  <img src="../../docs/images/sc-cot.png" alt="SC-CoT Workflow" width="200">
</div>

The Self-Consistent Chain of Thought (SC-CoT) workflow implements a robust reasoning approach that leverages multiple reasoning paths to arrive at a more reliable answer. Here's how it works:

### Core Components

#### 1. SCCoTWorkflow
The main workflow coordinator that:
- Manages the overall execution flow
- Handles input/output processing
- Coordinates with the reasoning component

#### 2. SCCoTReasoning
The core reasoning engine that implements the self-consistency algorithm:

##### a. Multiple Path Generation
- Generates `num` (default: 5) independent reasoning paths
- Supports two generation modes:
  * Parallel (`use_n=True`): Uses LLM's built-in parallel generation
  * Sequential (`use_n=False`): Generates paths one by one

##### b. Answer Extraction
Implements sophisticated answer extraction logic:
```python
def extract_final_answer(text):
    # 1. Searches for \boxed{} notation in the text
    # 2. If "Final Answer" marker exists:
    #    - Finds the closest \boxed{} to this marker
    # 3. Otherwise:
    #    - Uses the first \boxed{} found
    # 4. Extracts the content within the boxes
```

##### c. Majority Voting
Implements a robust voting mechanism:
```python
def get_most_common_answer(answers):
    # 1. Filters out None/invalid answers
    # 2. Counts occurrences of each unique answer
    # 3. Identifies answers with maximum occurrences
    # 4. If multiple answers tie for most common:
    #    - Randomly selects one of them
```

### Execution Flow
1. **Input Processing**
   - Receives query and optional ID
   - Prepares the reasoning context

2. **Path Generation**
   - For each path:
     * Formats the query with examples
     * Generates reasoning steps
     * Extracts final answer using \boxed{} notation

3. **Answer Aggregation**
   - Collects all extracted answers
   - Applies majority voting
   - Handles ties through random selection

4. **Output Formation**
   - Returns structured output with:
     * Original question
     * Final answer
     * Token usage statistics

### Key Features
- Robust answer extraction using \boxed{} notation
- Flexible generation modes (parallel/sequential)
- Sophisticated majority voting with tie handling
- Comprehensive token usage tracking
- Support for example-based prompting

## Running the Example

You can run the example in multiple ways:

### 1. Environment Setup
First, set up the required environment variables:
```bash
# Required environment variables
export custom_openai_endpoint='your_endpoint'  # LLM API endpoint
export custom_openai_key='your_key'           # API key
export custom_model_id='model_name'           # e.g., 'qwen2.5:7b'
export OMAGENT_MODE='lite'                    # or 'conductor'
```

### 2. Execution Modes

#### Lite Mode (Local Execution)
```bash
export OMAGENT_MODE="lite"
```
This mode runs the workflow locally without requiring a Conductor server.

#### Conductor Mode (Distributed Execution)
```bash
export OMAGENT_MODE="conductor"  # or just don't set OMAGENT_MODE
```
This mode requires a running Conductor server for workflow orchestration.

### 3. Usage Methods

#### A. Command Line Interface
```bash
cd examples/general_self_consist_cot
python run_cli.py
```

#### B. Programmatic Usage
```python
from omagent_core.advanced_components.workflow.self_consist_cot.workflow import SCCoTWorkflow
from omagent_core.clients.devices.programmatic import ProgrammaticClient

# Initialize workflow
workflow = SCCoTWorkflow()
workflow.set_input(query="Your question here")

# Initialize client
client = ProgrammaticClient(processor=workflow, config_path='path/to/configs')

# Process query
result = client.start_batch_processor(workflow_input_list=[{"query": "Your question here"}])
```

#### C. Web Interface
```python
python run_webpage.py
```
Launches a web interface for interactive usage.

#### D. App Interface
```python
python run_app.py
```
Launches an application interface for interactive usage.

#### E. Batch Processing
```python
python eval_batch.py
```
For processing multiple questions in batch mode, useful for evaluation or bulk processing.

##### Batch Processing Configuration
The batch processing mode requires additional environment variables:
```bash
export batch_size="1"          # Number of questions to process in each batch
export timeout="1000"          # Timeout in seconds for each batch
export dataset_name="math500"  # Name of the dataset
export dataset_path="/path/to/dataset.jsonl"  # Path to input JSONL file
export output_path="/path/to/output"         # Directory for output files
```

##### Input Format
The input dataset should be a JSONL file where each line contains:
```json
{
    "id": "unique_id",
    "question": "question text"
}
```

##### Output Format
The output will be saved in the format:
```json
{
    "id": "unique_id",
    "question": "original question",
    "last_output": "final answer",
    "prompt_tokens": number,
    "completion_tokens": number,
    "body": ""
}
```

##### Features
- Processes questions in configurable batch sizes
- Handles timeouts gracefully
- Resumes from last processed question if interrupted
- Tracks token usage
- Supports multiple LLM models through configuration

### 4. Configuration

The workflow can be configured using a YAML file. Example configuration:
```yaml
- name: SCCoTReasoning
  llm: ${sub|gpt4o}
  output_parser: 
    name: StrParser
  num: 5              # Number of reasoning paths
  use_n: True         # Use parallel generation
  example: |
    [Your example template]
```

## Example Usage and Output

```
Input: Which is bigger, 9.9 or 9.11?
Reasoning paths: [
    "9.9 is bigger than 9.11.",
    "9.9 is bigger than 9.11.",
    "9.9 is bigger than 9.11."
] 

Final answer: 9.9 is bigger than 9.11.
```

## Implementation Details

### Algorithm Overview
![SC-CoT Workflow](docs/images/sc-cot.png)

The Self-Consistent Chain of Thought (SC-CoT) workflow implements a robust reasoning approach that leverages multiple reasoning paths to arrive at a more reliable answer. Here's how it works:

### Core Components

#### 1. SCCoTWorkflow
The main workflow coordinator that:
- Manages the overall execution flow
- Handles input/output processing
- Coordinates with the reasoning component

#### 2. SCCoTReasoning
The core reasoning engine that implements the self-consistency algorithm:

##### a. Multiple Path Generation
- Generates `num` (default: 5) independent reasoning paths
- Supports two generation modes:
  * Parallel (`use_n=True`): Uses LLM's built-in parallel generation
  * Sequential (`use_n=False`): Generates paths one by one

##### b. Answer Extraction
Implements sophisticated answer extraction logic:
```python
def extract_final_answer(text):
    # 1. Searches for \boxed{} notation in the text
    # 2. If "Final Answer" marker exists:
    #    - Finds the closest \boxed{} to this marker
    # 3. Otherwise:
    #    - Uses the first \boxed{} found
    # 4. Extracts the content within the boxes
```

##### c. Majority Voting
Implements a robust voting mechanism:
```python
def get_most_common_answer(answers):
    # 1. Filters out None/invalid answers
    # 2. Counts occurrences of each unique answer
    # 3. Identifies answers with maximum occurrences
    # 4. If multiple answers tie for most common:
    #    - Randomly selects one of them
```

### Execution Flow
1. **Input Processing**
   - Receives query and optional ID
   - Prepares the reasoning context

2. **Path Generation**
   - For each path:
     * Formats the query with examples
     * Generates reasoning steps
     * Extracts final answer using \boxed{} notation

3. **Answer Aggregation**
   - Collects all extracted answers
   - Applies majority voting
   - Handles ties through random selection

4. **Output Formation**
   - Returns structured output with:
     * Original question
     * Final answer
     * Token usage statistics

### Key Features
- Robust answer extraction using \boxed{} notation
- Flexible generation modes (parallel/sequential)
- Sophisticated majority voting with tie handling
- Comprehensive token usage tracking
- Support for example-based prompting

## Dependencies
- OmAgent core components
- Redis (for Conductor mode)
- OpenAI-compatible LLM API

## Citation
```
@inproceedings{DBLP:conf/iclr/0002WSLCNCZ23,
  author       = {Xuezhi Wang and
                  Jason Wei and
                  Dale Schuurmans and
                  Quoc V. Le and
                  Ed H. Chi and
                  Sharan Narang and
                  Aakanksha Chowdhery and
                  Denny Zhou},
  title        = {Self-Consistency Improves Chain of Thought Reasoning in Language Models},
  booktitle    = {{ICLR}},
  publisher    = {OpenReview.net},
  year         = {2023}
}
```