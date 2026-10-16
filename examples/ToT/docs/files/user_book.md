# ToT User Book

There are many parameter designs in the official implementation of tot, and these parameters are still available in the OmAgent version.


## Thought Decomposition

Regarding the part about mind splitting, the basic parameters of tot are set in the workflow config file, including the maximum number of layers of the mind tree, the maximum number of execution steps, the search algorithm, and if it is bfs, the number of pruned branches to be retained. 

The settings are as follows:

```yml
- name: ThoughtDecomposition
  params:
    max_depth: 6
    max_steps: 6
    search_type: bfs
    b: 1
```
| Name     | Type | Description |
| -------- | ----- | ---- |
| max_depth | int |  The maximum depth of the thought tree. |
| max_steps | int |  The maximum steps of the thought tree. |
| search_type | str |  The search type of the thought tree, it can be 'bfs' or 'dfs'. |
| b | int |  The number of kept branches for each node after pruning. |

## Thought Generator

In the part of thought generation, the official thought generation has two modes: "sample" and "propose". In the general implementation, we merge them into one, because both modes are inferences for the next step, but sample only returns one result, and propose returns as many possibilities as possible. The other parameter setting is the number of LLM inferences n. This needs to be set in the config of LLM.

workflow config:
It is worth mentioning that if llm supports the parameter n, then support_n can be added to reduce the use of tokens.
```yml
- name: ThoughtGenerator
  llm: ${sub|thought_generator}
  support_n: true
```

thought_generator LLM config:

```yml
name: OpenaiGPTLLM
model_id: ${env| custom_model_id}
api_key: ${env| custom_openai_key, openai_api_key}
endpoint: ${env| custom_openai_endpoint, https://api.openai.com/v1}
temperature: 0.0
max_tokens: 2048
response_format: json_object
n: 1
```
| Name     | Type | Description |
| -------- | ----- | ---- |
| model_id | str |  The model id of the LLM. |
| api_key | str |  The api key of the LLM. |
| endpoint | str |  The endpoint of the LLM. |
| temperature | float |  The temperature of the LLM. |
| max_tokens | int |  The max tokens of the LLM. |
| response_format | str |  The response format of the LLM. |
| n | int |  The number of inferences of the LLM. |


## State Evaluator

The state evaluator is the part that evaluates the state of the current thought. The basic parameters are the same as the official implementation. 

workflow config:

```yml
- name: StateEvaluator
  llm: ${sub|state_evaluator}
  support_n: true
  params:
    evaluation_type: vote
```

state_evaluator LLM config:

```yml
name: OpenaiGPTLLM
model_id: ${env| custom_model_id}
api_key: ${env| custom_openai_key, openai_api_key}
endpoint: ${env| custom_openai_endpoint, https://api.openai.com/v1}
temperature: 0.0
max_tokens: 2048
response_format: json_object
n: 3
```
| Name     | Type | Description |
| -------- | ----- | ---- |
| model_id | str |  The model id of the LLM. |
| api_key | str |  The api key of the LLM. |
| endpoint | str |  The endpoint of the LLM. |
| temperature | float |  The temperature of the LLM. |
| max_tokens | int |  The max tokens of the LLM. |
| response_format | str |  The response format of the LLM. |
| n | int |  The number of inferences of the LLM. |


## Search Algorithm

The search algorithm is the part that searches for the next thought. The basic parameters are the same as the official implementation. It is worth mentioning that because it is a universal format implementation, the maximum depth required for different tasks may be different, so a step is added to use the model to determine whether the task is completed.

workflow config:

```yml
- name: SearchAlgorithm
  domain: ${env| custom_domain}
  llm: ${sub|json_res}
  use_llm_completion: true
```

## Addition of few shot example

Sometimes, in order for the model to better understand how to split the task and how to execute it, it is necessary to pass in examples. This can be set like:

```python
# Initialize simple VQA workflow
workflow = ConductorWorkflow(name='ToT_Workflow_test')

tot_workflow = ToTWorkflow()
tot_workflow.set_tot(
    requirements = "you requirements",
    thought_generator_examples = "your few shot examples of thought generator",
    state_evaluator_examples = "your few shot examples of state evaluator",
)

tot_workflow.set_input(
    query = "your query",
)

workflow >> tot_workflow
```


