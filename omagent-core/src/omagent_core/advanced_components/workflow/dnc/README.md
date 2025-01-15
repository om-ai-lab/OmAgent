# Divide-and-Conquer Operator
Divide-and-Conquer (DnC) is a workflow operator that decomposes a complex task into multiple sub-tasks, and then conquers each sub-task to complete the original task. 

You can refer to the example in the `examples/general_dnc` directory to understand how to use this operator.

# Inputs, Outputs and configs

## Inputs:
The inputs that the Divide-and-Conquer (DnC) operator requires are as follows:
| Name     | Type | Required | Description |
| -------- | ----- | ----- | ---- |
| query | str | true |  The name of the user |

## Outputs:
The outputs that the Divide-and-Conquer (DnC) operator returns are as follows:
| Name     | Type | Description |
| -------- | ----- | ---- |
| dnc_structure | dict |  The tree structured data of the dnc workflow, including all (sub)tasks and their outputs. |
| last_output | str |  The output of the last task. |

## Configs:
The config of the Divide-and-Conquer (DnC) operator is as follows, you can simply copy and paste the following config into your project as a dnc_workflow.yml file.
```yml
- name: ConstructDncPayload
- name: StructureUpdate
- name: TaskConqueror
  llm: ${sub|json_res}
  tool_manager: ${sub|all_tools}
  output_parser: 
    name: StrParser
- name: TaskDivider
  llm: ${sub|json_res}
  tool_manager: ${sub|all_tools}
  output_parser: 
    name: StrParser
- name: TaskRescue
  llm: ${sub|text_res}
  tool_manager: ${sub|all_tools}
  output_parser: 
    name: StrParser
- name: TaskExitMonitor

```