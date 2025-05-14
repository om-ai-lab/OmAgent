from typing import List

from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task

from omagent_core.advanced_components.workflow.sc_cot.agent.sc_cot_reasoning.sc_cot_reasoning import SCCoTReasoning


class SCCoTWorkflow( ConductorWorkflow ):

    def __init__( self ):
        super().__init__( name='sc_cot_workflow' )

    def set_input( self, query: str, id: int = 0 ):
        """
        Sets the input parameters for the workflow.
        Args:
            query (str): The query string to be processed.
            cot_method (str, optional): The method to be used for chain-of-thought (CoT) processing. Defaults to 'few_shot'.
            cot_examples (List[dict], optional): A list of examples for CoT processing. Defaults to None.
            id (int, optional): An identifier for the workflow instance. Defaults to 0.
        Returns:
            None
        """

        self.id = id
        self.query = query

        self._configure_tasks()
        self._configure_workflow()

    def _configure_tasks( self ):
        # reasoning task for reasoning process
        self.reasoning_task = simple_task(
            task_def_name=SCCoTReasoning,
            task_reference_name='SCCoT_Reasoning',
            inputs={
                'id': self.id,
                'query': self.query
            }
        )

    def _configure_workflow( self ):
        # configure workflow execution flow
        self >> self.reasoning_task

        self.id = self.reasoning_task.output( 'id' )
        self.question = self.reasoning_task.output( 'question' )
        self.last_output = self.reasoning_task.output( 'last_output' )
        self.prompt_tokens = self.reasoning_task.output( 'prompt_tokens' )
        self.completion_tokens = self.reasoning_task.output( 'completion_tokens' )
