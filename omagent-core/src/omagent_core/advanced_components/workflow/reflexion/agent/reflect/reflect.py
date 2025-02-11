from pathlib import Path
from typing import Dict, Any, List

from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from omagent_core.utils.registry import registry
from pydantic import Field

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class Reflect(BaseLLMBackend, BaseWorker):
    """Worker for reflection process in React Pro workflow"""
    
    critical_template: str = Field(default="")
    reflect_template: str = Field(default="")
    reflect_examples: str = Field(default="")
    max_turns: int = Field(default=2)

    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("user_prompt.prompt"),
                role="user"
            ),
        ]
    )
        
    def _run(self, react_output: str, *args, **kwargs) -> Dict[str, Any]:
        # Get state from STM
        state = self.stm(self.workflow_instance_id)   
        query = state.get('query', '')
        token_usage = state.get('token_usage', {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0
        })

        # Handle max_turns
        state['turns'] = state.get('turns', 0) + 1

        if state['turns'] >= self.max_turns:
            return {
                'reflection': 'No more turns',
                'should_retry': False,
                'react_output': react_output,
            }

        context = state.get('context', '')     

        critical_prompt = self.critical_template.replace("{{context}}", context)
        # Get reflection from LLM
        response = self.simple_infer(
            query=query,
            context=critical_prompt
        )
        if 'usage' in response:
            token_usage['prompt_tokens'] += response['usage']['prompt_tokens']
            token_usage['completion_tokens'] += response['usage']['completion_tokens']
            token_usage['total_tokens'] += response['usage']['total_tokens']
            # Update token_usage in STM
            state.update({'token_usage': token_usage})
        
        # Process response
        critical_result = response['choices'][0]['message']['content']
        
        # Record output information
        self.callback.info(
            agent_id=self.workflow_instance_id,
            progress='critical',
            message=f'critical: {critical_result}'
        )
        
        if "False" in critical_result:
            return {
                'reflection': 'No more turns',
                'should_retry': False,
                'react_output': react_output,
            }

        # Initialize reflection add_history(line)
        reflection_history = state.get('reflection_history', [])
        
        reflection_prompt = self.reflect_template.replace("{question}", query).replace("{scratchpad}",context).replace("{examples}", self.reflect_examples)
        # Get reflection from LLM
        response = self.simple_infer(
            query=query,
            context=reflection_prompt
        )
        
        if 'usage' in response:
            token_usage['prompt_tokens'] += response['usage']['prompt_tokens']
            token_usage['completion_tokens'] += response['usage']['completion_tokens']
            token_usage['total_tokens'] += response['usage']['total_tokens']
            # Update token_usage in STM
            state.update({'token_usage': token_usage})
        # Process response
        reflection = response['choices'][0]['message']['content']
        
        # Update reflection history
        reflection_history.append(reflection)
        state['reflection_history'] = reflection_history
        
        # Record output information
        self.callback.info(
            agent_id=self.workflow_instance_id,
            progress='Reflect',
            message=f'Reflection: {reflection}'
        )
        
        # Analyze if we need to retry
        should_retry = "incorrect" in reflection.lower() or "wrong" in reflection.lower()
        state['context'] = ""
        return {
            'reflection': reflection,
            'should_retry': should_retry,
            'react_output': react_output,
        } 