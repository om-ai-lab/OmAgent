# Tree-of-Thought Operator
ToT(Tree of Thought) is a workflow operator that returns multiple possible proposals for each step of a task and selects the most promising option after evaluation to ultimately solve the task.

You can refer to the example in the `examples/ToT` directory to understand how to use this operator.

# Inputs, Outputs and configs

## Inputs:
The inputs that the Tree-of-Thought (ToT) operator requires are as follows:
| Name     | Type | Required | Description |
| -------- | ----- | ----- | ---- |
| problem | str | true |  The problem to be solved |
| requirements | str | true |  The requirements for the problem |
| few_shots | str | false |  The few shots for the problem, you can input some examples to help the model understand how to solve the problem |
## Outputs:
The outputs that the Tree-of-Thought (ToT) operator returns are as follows:
| Name     | Type | Description |
| -------- | ----- | ---- |
| result | dict |  The result of the ToT workflow. It includes the last output, prompt tokens, completion tokens, and the question that the model is trying to solve. |

## Configs:
The config of the Tree-of-Thought (ToT) operator is as follows, you can simply copy and paste the following config into your project as a tot_workflow.yml file.
```yml
- name: ThoughtDecomposition
  domain: ${env| custom_domain}
  params:
    max_depth: 6
    max_steps: 6
    search_type: bfs
    b: 1
- name: ThoughtGenerator
  domain: ${env| custom_domain}
  llm: ${sub|thought_generator}
- name: StateEvaluator
  domain: ${env| custom_domain}
  llm: ${sub|state_evaluator}
  params:
    evaluation_type: vote
- name: SearchAlgorithm
  domain: ${env| custom_domain}
  llm: ${sub|json_res}
  use_llm_completion: true

```
The Tree-of-Thought (ToT) operator settings are as follows:
| Name     | Type | Description |
| -------- | ----- | ---- |
| max_depth | int |  The maximum depth of the thought tree. |
| max_steps | int |  The maximum steps of the thought tree. |
| search_type | str |  The search type of the thought tree, it can be 'bfs' or 'dfs'. |
| b | int |  The number of kept branches for each node after pruning. |
| evaluation_type | str |  The evaluation type of the thought tree, it can be 'vote' or 'value'. |
| use_llm_completion | bool |  Whether to use the llm to determine the completion of the tot workflow. |
