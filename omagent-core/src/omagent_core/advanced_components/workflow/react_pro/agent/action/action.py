from pathlib import Path
from typing import List
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.utils.registry import registry
from pydantic import Field

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class Action(BaseLLMBackend, BaseWorker):
    """Action worker that determines the next step in ReAct chain"""
    
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("user_prompt.prompt"), 
                role="user"
            ),
        ]
    )

    def _run(self, *args, **kwargs):
        """Process the query using ReAct approach"""
        # Get context and other states from STM
        state = self.stm(self.workflow_instance_id)
        context = state.get('context', '')
        query = state.get('query', '')
        id = state.get('id', '')
        token_usage = state.get('token_usage', {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0
        })
        
        # Get current step number
        current_step = state.get('step_number', 1)
        
        # Record output information
        self.callback.info(
            agent_id=self.workflow_instance_id, 
            progress='Action', 
            message=f'Step {current_step}'
        )
        
        # build prompt
        full_prompt = f"{context}\nAction {current_step}:"
        
        # Add dynamic step number hint
        full_prompt += f"\nNote: Only output Action {current_step}."
        
        # Get response
        response = self.simple_infer(query=query, context=full_prompt)
        
        # Update token usage
        if 'usage' in response:
            token_usage['prompt_tokens'] += response['usage']['prompt_tokens']
            token_usage['completion_tokens'] += response['usage']['completion_tokens']
            token_usage['total_tokens'] += response['usage']['total_tokens']
            # Update token_usage in STM
            state.update({'token_usage': token_usage})
        
        # Process non-streaming response
        output = response['choices'][0]['message']['content']
        
        # Check if it's a Finish action
        is_final = 'Finish[' in output
        
        # Record output information
        self.callback.info(
            agent_id=self.workflow_instance_id, 
            progress='Action', 
            message=f'Action {current_step}: {output}'
        )
        
        # Update context and store in STM
        new_context = f"{context}\nAction {current_step}: {output}"
        state.update({
            'context': new_context,
            'token_usage': token_usage
        })
        
        return {
            'output': output,
            'step_number': current_step,
            'is_final': is_final,
            'query': query,
            'id': id,
            'token_usage': token_usage,
            'body': state.get('body', {})
        }
    
        