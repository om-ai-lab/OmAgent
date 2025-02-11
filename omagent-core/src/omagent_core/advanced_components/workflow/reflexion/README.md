# Reflexion Operator
Reflexion is an advanced workflow operator that implements self-reflection for continuous improvement in complex reasoning tasks. It maintains an iterative process of reasoning, execution, evaluation, and reflection to achieve better results.

You can refer to the example in the `examples/reflexion` directory to understand how to use this operator.

# Inputs, Outputs and configs

## Inputs:
The inputs that the Reflexion operator requires are as follows:
| Name     | Type | Required | Description |
| -------- | ----- | ----- | ---- |
| query | str | true | The question or task to be solved |
| id | str | false | A unique identifier for the conversation. If not provided, a default empty string will be used |

## Outputs:
The outputs that the Reflexion operator returns are as follows:
| Name     | Type | Description |
| -------- | ----- | ---- |
| output | str | The final answer or response |
| query | str | The original question |
| id | str | The conversation identifier |
| token_usage | dict | Token usage statistics for the conversation |
| reflections | list | List of reflection steps taken during reasoning |

## Configs:
The config of the Reflexion operator is as follows, you can simply copy and paste the following config into your project as a reflexion_workflow.yml file.
```yml
- name: Think
  llm: ${sub|text_res}
  output_parser: 
    name: StrParser
- name: Action
  llm: ${sub|text_res}
  output_parser: 
    name: StrParser
- name: WikiSearch
  llm: ${sub|text_res}
  output_parser:
    name: StrParser
- name: ReactOutput
  llm: ${sub|text_res}
  output_parser:
    name: StrParser
- name: Reflect
  llm: ${sub|text_res}
  output_parser:
    name: StrParser
- name: FinalOutput
``` 