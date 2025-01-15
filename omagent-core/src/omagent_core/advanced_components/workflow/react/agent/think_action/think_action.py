from pathlib import Path
from typing import List, Any
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.utils.registry import registry
from pydantic import Field

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class ThinkAction(BaseLLMBackend, BaseWorker):
    """Combined Think and Action worker that implements ReAct (Reasoning and Acting) approach"""
    
    # debug_mode: bool = Field(default=False)
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

    def _run(self, query: str, id: str = "", next_step: str = "Thought", *args, **kwargs):
        """Process the query using ReAct approach with combined Think and Action steps"""
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
        
        # Get current step number
        current_step = state.get('step_number', 1)

        # Get model call parameters
        message = self.prep_prompt([{"question": query}])
        body = self.llm._msg2req(message[0])
        self.stm(self.workflow_instance_id)["body"] = body

        # Record input information
        self.callback.info(
            agent_id=self.workflow_instance_id, 
            progress='ThinkAction', 
            message=f'Step {current_step}'
        )

        # Build prompt
        full_prompt = f"{context}\n{next_step} {current_step}:" if context else f"{self.example}\nQuestion: {query}\n{next_step} {current_step}:"
        
        try:
            # First try to get thought and action in one call
            response = self.simple_infer(
                query=query, 
                context=full_prompt,
                stop=[f"\nObservation {current_step}:"]
            )
            output = response['choices'][0]['message']['content']
            if "\nObservation" in output:
                output = output.split("\nObservation")[0]
            try:
                # Try to separate thought and action
                thought, action = output.strip().split(f"\nAction {current_step}: ")
            except:
                # If separation fails, make a second attempt
                thought = output.strip().split('\n')[0]
                action_response = self.simple_infer(
                    query=query,
                    context=f"{full_prompt}\n{thought}\nAction {current_step}:",
                    stop=["\n"]
                )
                if "\n" in action_response['choices'][0]['message']['content']:
                    action_response['choices'][0]['message']['content'] = action_response['choices'][0]['message']['content'].split("\n")[0]
                action = action_response['choices'][0]['message']['content'].strip()
            
            # Update token usage
            if 'usage' in response:
                token_usage['prompt_tokens'] += response['usage']['prompt_tokens']
                token_usage['completion_tokens'] += response['usage']['completion_tokens']
                token_usage['total_tokens'] += response['usage']['total_tokens']
            
            # Combine output
            output = f"{thought}\nAction {current_step}: {action}"
            
        except Exception as e:
            self.callback.error(
                agent_id=self.workflow_instance_id,
                progress='ThinkAction Error',
                message=f'Error: {str(e)}'
            )
            raise
        
        # Check if it's a Finish action
        is_final = 'Finish[' in action
        
        # Record output information
        self.callback.info(
            agent_id=self.workflow_instance_id, 
            progress='ThinkAction', 
            message=f'Step {current_step}: {output}'
        )
        
        # Update context and store in STM
        new_context = f"{context}\n{next_step} {current_step}: {output}" if context else f"{self.example}\nQuestion: {query}\n{next_step} {current_step}: {output}"
        state.update({
            'context': new_context,
            'query': query,
            'id': id,
            'token_usage': token_usage
        })
        
        return {
            'output': output,
            'action': action,
            'step_number': current_step,
            'is_final': is_final,
            'query': query,
            'id': id,
            'token_usage': token_usage,
            'body': state.get('body', {}),
            'max_steps': self.max_steps
        }
        