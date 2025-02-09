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
    
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("sys_prompt.prompt"),
                role="system"
            ),
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("user_prompt.prompt"),
                role="user"
            ),
        ]
    )
        
    def _run(self, query: str, react_output: str, context: str, *args, **kwargs) -> Dict[str, Any]:
        """Run reflection process on the action output
        
        Args:
            query: The original query
            react_output: The output from React process
            workflow_id: Workflow instance ID
            
        Returns:
            Dict containing reflection results and whether to retry
        """
        # Get state from STM
        state = self.stm(self.workflow_instance_id)


        state = self.stm(self.workflow_instance_id)
        context = state.get('context', '')          
        # Initialize reflection add_history(line)
        reflection_history = state.get('reflection_history', [])
        
        # Prepare message for LLM
        message = self.prep_prompt([{
            "query": query,
            "action_output": react_output,
            "reflection_history": reflection_history
        }])
        
        # Get reflection from LLM
        response = self.simple_infer(
            query=query,
            context=message[0]
        )
        
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
        
        return {
            'reflection': reflection,
            'should_retry': should_retry,
            'reflection_history': reflection_history
        } 