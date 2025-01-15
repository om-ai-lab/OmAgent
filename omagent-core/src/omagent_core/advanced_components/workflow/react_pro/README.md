# React Pro Operator
React Pro is an advanced workflow operator that implements the ReAct (Reasoning + Acting) paradigm for complex question answering tasks. It separates the thinking and action processes into distinct components for better control and observation.

You can refer to the example in the `examples/react_pro` directory to understand how to use this operator.

# Inputs, Outputs and configs

## Inputs:
The inputs that the React Pro operator requires are as follows:
| Name     | Type | Required | Description |
| -------- | ----- | ----- | ---- |
| query | str | true | The question or task to be solved |
| id | str | false | A unique identifier for the conversation. If not provided, a default empty string will be used |

## Outputs:
The outputs that the React Pro operator returns are as follows:
| Name     | Type | Description |
| -------- | ----- | ---- |
| output | str | The final answer or response |
| query | str | The original question |
| id | str | The conversation identifier |
| token_usage | dict | Token usage statistics for the conversation |

## Configs:
The config of the React Pro operator is as follows, you can simply copy and paste the following config into your project as a react_pro_workflow.yml file.
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
- name: ReactOutput
```

