from pathlib import Path
from typing import List, Any
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.utils.registry import registry
from pydantic import Field

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class Think(BaseLLMBackend, BaseWorker):
    """Think worker that implements ReAct (Reasoning and Acting) approach"""
    
    example: str = Field(default="")
    max_steps: int = Field(default=8)
    
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("user_prompt.prompt"), 
                role="user"
            ),
        ]
    )

    def _run(self, query: str, *args, **kwargs):
        """Process the query using ReAct approach"""
        # Get context from STM
        state = self.stm(self.workflow_instance_id)
        context = state.get('context', '')

        # Initialize token_usage
        token_usage = state.get('token_usage', {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0
        })

        # Initialize step_number for new conversation (empty context)
        if not context:
            state['step_number'] = 1
        
        current_step = state.get('step_number', 1)
        
        #Record input information
        self.callback.info(
            agent_id=self.workflow_instance_id, 
            progress='Think', 
            message=f'Step {current_step}'
        )
         
        reflections = state.get('reflection_history', '')

        # Build prompt
        full_prompt = f"{context}\nThought {current_step}:" if context else f"{self.example}\n{reflections}\nQuestion: {query}\nThought {current_step}:"
        
        # Get response
        response = self.simple_infer(query=query, context=full_prompt)

        # Get model call parameters
        message = self.prep_prompt([{"question": query}])
        body = self.llm._msg2req(message[0])
        state["body"] = body
        
        # Process non-streaming response
        output = response['choices'][0]['message']['content'].split('\n')[0]
        
        # Update token usage
        if 'usage' in response:
            token_usage['prompt_tokens'] += response['usage']['prompt_tokens']
            token_usage['completion_tokens'] += response['usage']['completion_tokens']
            token_usage['total_tokens'] += response['usage']['total_tokens']
            # Update token_usage in STM
            state.update({'token_usage': token_usage})
    
        # Record output information
        self.callback.info(
            agent_id=self.workflow_instance_id, 
            progress='Think', 
            message=f'Thought {current_step}: {output}'
        )
        
        # Update context and store in STM
        new_context = f"{context}\nThought {current_step}: {output}" if context else f"{self.example}\n{reflections}\nQuestion: {query}\nThought {current_step}: {output}"
        state.update({
            'context': new_context,
            'query': query,
            'step_number': current_step  # Update step number
        })

        return {
            'response': output,
            'step_number': current_step,
            'max_steps': self.max_steps
        } 