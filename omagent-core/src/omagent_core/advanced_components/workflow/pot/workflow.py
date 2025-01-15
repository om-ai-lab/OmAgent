from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.advanced_components.workflow.pot.agent.executor.PoTExecutor import PoTExecutor    
from omagent_core.advanced_components.workflow.pot.agent.choice_extractor.choice_extractor import ChoiceExtractor
from typing import List

class PoTWorkflow(ConductorWorkflow):
    """Program-of-Thought workflow that executes math word problem solving tasks.
    
    This workflow configures and executes the PoT executor to solve math problems
    by generating and running Python code.
    """
    def __init__(self):
        super().__init__(name='pot_workflow')
        
    def set_input(self, query: str, examples: str = None, options: str = None):
        """Set input parameters and configure workflow.
        
        Args:
            query: Math word problem text to solve
            examples: Optional few-shot examples to guide code generation
            options: Optional list of options to choose from
        """
        self.query = query
        self.examples = examples
        self.options = options
        self._configure_tasks()
        self._configure_workflow()

    def _configure_tasks(self):
        """Configure the PoT executor task with input parameters."""
        self.pot_executor_task = simple_task(
            task_def_name=PoTExecutor,  
            task_reference_name='PoT_executor',
            inputs={'query': self.query, 'examples': self.examples, 'options': self.options}
        )
        self.choice_extractor_task = simple_task(
            task_def_name=ChoiceExtractor,  
            task_reference_name='choice_extractor',
            inputs={'query': self.query, 
                    'examples': self.examples, 
                    'options': self.options, 
                    'prediction': self.pot_executor_task.output('last_output'),
                    'completion_tokens': self.pot_executor_task.output('completion_tokens'),
                    'prompt_tokens': self.pot_executor_task.output('prompt_tokens')}
        )

    def _configure_workflow(self):
        """Configure workflow execution flow and output.
        
        Sets up task dependencies and captures the final numerical answer
        from the executor's output.
        """
        self >> self.pot_executor_task >> self.choice_extractor_task
        self.last_output = self.choice_extractor_task.output('last_output')
        self.completion_tokens = self.choice_extractor_task.output('completion_tokens')
        self.prompt_tokens = self.choice_extractor_task.output('prompt_tokens')
