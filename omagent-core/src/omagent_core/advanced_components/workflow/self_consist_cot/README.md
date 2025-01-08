# Self-Consistent Chain-of-Thought (CoT) Workflow

A workflow component that implements self-consistent chain-of-thought reasoning for complex problem-solving tasks. This component generates multiple reasoning paths and aggregates them to produce a more reliable final answer.

## Overview

The Self-Consistent CoT workflow consists of three main stages:

1. **CoT Reasoning**: Generates multiple reasoning paths for the given question
2. **CoT Extract**: Extracts final answers from each reasoning path
3. **CoT Conclusion**: Analyzes extracted answers to produce a final consensus answer

## Usage

```python
from omagent_core.advanced_components.workflow.self_consist_cot.workflow import SelfConsistentWorkflow

# Initialize the workflow
workflow = SelfConsistentWorkflow()

# Set input parameters
workflow.set_input(
    user_question="Your question here",  # The question to be answered
    path_num=5                          # Number of reasoning paths to generate
)
```

## Components

### COTReasoning

Generates multiple independent reasoning paths for the given question. Each path shows step-by-step reasoning leading to an answer.

### COTExtract

Extracts final answers from each reasoning path, focusing on the conclusion rather than the intermediate steps.

### COTConclusion

Analyzes all extracted answers to determine the most consistent and reliable final answer.

## Example

Here's a simple example using the GSM8K math dataset:

```python
# Question: "Janet's ducks lay 16 eggs per day. She eats three for breakfast every morning and 
# bakes muffins for her friends every day with four. She sells the remainder at the farmers' 
# market daily for $2 per fresh duck egg. How much money does she make per day at the farmers' market?"

workflow = SelfConsistentWorkflow()
workflow.set_input(user_question=question, path_num=5)
```

The workflow will:
1. Generate 5 different reasoning paths
2. Extract answers from each path
3. Analyze the answers to produce a final consensus

## Performance

The self-consistent approach helps improve accuracy by:
- Generating multiple independent reasoning attempts
- Cross-validating answers across different paths
- Reducing the impact of individual reasoning errors

## Dependencies

- OpenAI GPT models for reasoning
- Redis for state management
- OmAgent core components