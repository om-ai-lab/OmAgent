# Program-of-Thought (PoT) Operator
Program-of-Thought (PoT) is a workflow operator that solves math word problems by generating and executing Python code. It consists of two main components:

1. A PoT Executor that uses an LLM to generate Python code implementing the solution steps, safely executes the code in an isolated environment, and extracts the numerical answer.

2. A Choice Extractor that processes multiple choice questions by analyzing the generated answer against provided options using an LLM.

You can refer to the examples in the `examples/PoT` directory to understand how to use this operator.

# Inputs, Outputs and Configs

## Inputs:
The inputs that the Program-of-Thought (PoT) operator requires are as follows:
| Name     | Type | Required | Description |
| -------- | ----- | ----- | ---- |
| query | str | true | The math word problem text to solve |
| examples | str | false | Few-shot examples to guide code generation. If provided, uses a specialized few-shot prompt template |
| options | str | false | Multiple choice options. If provided, triggers the Choice Extractor to analyze the answer against these options |

## Outputs:
The outputs that the Program-of-Thought (PoT) operator returns are as follows:
| Name     | Type | Description |
| -------- | ----- | ---- |
| last_output | Union[float,str] | For regular problems: numerical answer as float. For multiple choice: selected option as string |
| completion_tokens | int | Cumulative number of tokens in LLM completions |
| prompt_tokens | int | Cumulative number of tokens in LLM prompts |

## Configs:
The config of the Program-of-Thought (PoT) operator is as follows, you can simply copy and paste the following config into your project as a pot_workflow.yml file.
```yml
- name: PoTExecutor
  llm: ${sub| gpt}
- name: ChoiceExtractor
  llm: ${sub| gpt}
```