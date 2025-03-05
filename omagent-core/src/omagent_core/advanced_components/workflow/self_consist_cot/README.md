# Self-Consistent Chain-of-Thought (CoT) Workflow

A workflow component that implements self-consistent chain-of-thought reasoning for complex problem-solving tasks. This component generates multiple reasoning paths and aggregates them to produce a more reliable final answer through majority voting.

## Overview

The Self-Consistent CoT workflow consists of a single main component that handles the entire process:

1. **SCCoTReasoning**: Generates multiple reasoning paths and extracts the most common answer as the final result

## Inputs, Outputs and Configs

### Inputs:
The inputs that the Self-Consistent CoT workflow requires are as follows:
| Name     | Type | Required | Description |
| -------- | ----- | ----- | ---- |
| id | int | false | The identifier for the task (defaults to 0) |
| query | str | true | The question or task to be solved |

### Outputs:
The outputs that the Self-Consistent CoT workflow returns are as follows:
| Name     | Type | Description |
| -------- | ----- | ---- |
| id | int | The task identifier |
| question | str | The original input question |
| last_output | str | The final concluded answer (most common answer from all runs) |
| prompt_tokens | int | Number of prompt tokens used |
| completion_tokens | int | Number of completion tokens used |
| body | str | The response body (empty in current implementation) |

### Configs:
The config of the Self-Consistent CoT workflow should be defined in a YAML file. Here's an example configuration from sc_cot_workflow.yml:
```yml
- name: SCCoTReasoning
  llm: ${sub|gpt4o}
  output_parser: 
    name: StrParser
  num: 5
  use_n: True
  example: |
    [Example template with math problems]
```

#### Configuration Parameters:
| Parameter | Type | Description |
| --------- | ---- | ----------- |
| name | str | The name of the reasoning component, must be "SCCoTReasoning" |
| llm | str | The language model to use, specified as a substitution variable (e.g., ${sub\|gpt4o}) |
| output_parser.name | str | The parser to process LLM outputs, "StrParser" is used for string output parsing |
| num | int | Number of reasoning attempts to generate (default: 5) |
| use_n | bool | When True, uses LLM's n parameter for parallel generation; when False, generates sequentially |
| example | str | Template containing example problems and their solutions to guide the model's reasoning format |

