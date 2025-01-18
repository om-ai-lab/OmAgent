# Agentic Operators in OmAgent

## Introduction
The `agentic operators` module is integrated within the OmAgent framework, providing a suite of mature algorithms designed to tackle specific problems effectively. These operators enhance the capabilities of agents by incorporating advanced reasoning and acting techniques.

### Integration and Usage

These operators are seamlessly integrated into OmAgent, allowing users to import them as tools for various steps within an application. For instance, an operator can replace a specific reasoning step in an application, thereby enhancing the agent's performance across diverse tasks.

### Benefits

By leveraging these classic operators, users can easily improve their agents' performance in a wide range of tasks, making OmAgent a versatile and powerful tool for developing intelligent agents.

## Operator List
- **CoT: Chain-of-thought prompting elicits reasoning in large language models** ([Paper](https://arxiv.org/abs/2201.11903) | [Operator](../../omagent-core/src/omagent_core/advanced_components/workflow/cot))  
  Enhances response quality by encouraging more in-depth reasoning through prompts.   
 
- **SC-CoT: Self-Consistency Improves Chain of Thought Reasoning in Language Models** ([Paper](https://arxiv.org/abs/2203.11171) | [Operator](../../omagent-core/src/omagent_core/advanced_components/workflow/self_consist_cot))  
  Improves reasoning consistency in language models. 
  
- **PoT: Program of thoughts prompting: Disentangling computation from reasoning for numerical reasoning tasks** ([Paper](https://arxiv.org/abs/2211.12588) | [Operator](../../omagent-core/src/omagent_core/advanced_components/workflow/pot))  
  Disentangles computation from reasoning for numerical reasoning tasks. 
  
- **ReAct: ReAct: Synergizing Reasoning and Acting in Language Models** ([Paper](https://arxiv.org/abs/2210.03629) | [ReAct Operator](../../omagent-core/src/omagent_core/advanced_components/workflow/react) | [ReAct-Pro Operator](../../omagent-core/src/omagent_core/advanced_components/workflow/react_pro))  
  Combines reasoning with acting, allowing agents to utilize external tools and information in real-time to solve problems.