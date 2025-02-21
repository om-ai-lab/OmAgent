# Reasoning via Planning (RAP) Operator

RAP is a workflow operator that performs reasoning by treating it as a planning problem with a world model. It uses Monte Carlo Tree Search (MCTS) to explore the reasoning space and find high-reward reasoning paths.

Refer to the example in the `examples/rap` directory to understand how to use this operator.

## Overview

RAP repurposes the language model as both:
1. A world model - to predict states and simulate outcomes
2. A reasoning agent - to explore and evaluate reasoning paths

The algorithm uses MCTS to strategically explore the vast reasoning space with a proper balance between exploration and exploitation.

## Inputs, Outputs and Configs

### Inputs:
| Name | Type | Required | Description |
| ---- | ---- | -------- | ----------- |
| query | str | true | The reasoning query/problem to solve |

### Outputs:
| Name | Type | Description |
| ---- | ---- | ----------- |
| final_answer | str | The final answer/solution to the query |

### Configs:
The config of the RAP operator should be defined in a `rap_workflow.yml` file:

```yml
- name: InputInterface
- name: Selection 
- name: Expansion
  llm: ${sub|gpt}
- name: SimulationPreProcess
- name: SimulationPostProcess
- name: BackPropagation
- name: MCTSCompletionCheck
```

## References

[1] Hao, S., Gu, Y., Ma, H., Hong, J. J., Wang, Z., Wang, D. Z., & Hu, Z. (2023). Reasoning with Language Model is Planning with World Model. arXiv preprint arXiv:2305.14992. 