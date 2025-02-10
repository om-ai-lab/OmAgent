import os
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task

from omagent_core.advanced_components.workflow.ToT.agent.thought_decomposition.thought_decomposition import ThoughtDecomposition
from omagent_core.advanced_components.workflow.ToT.agent.thought_generator.thought_generator import ThoughtGenerator
from omagent_core.advanced_components.workflow.ToT.agent.state_evaluator.state_evaluator import StateEvaluator
from omagent_core.advanced_components.workflow.ToT.agent.search_algorithm.search_algorithm import SearchAlgorithm
from omagent_core.engine.workflow.task.do_while_task import DoWhileTask

class ToTWorkflow(ConductorWorkflow):
    """Implementation of Tree of Thoughts (ToT) workflow"""
    
    def __init__(self):
        """Initialize ToT workflow"""
        super().__init__(name='tot_workflow')
        
    def set_tot(self, requirements: str, thought_generator_examples: str=None, state_evaluator_examples: str=None):
        """Set basic parameters for ToT workflow
        Args:
            requirements: Task requirements
            thought_generator_examples: Examples for thought generator
            state_evaluator_examples: Examples for state evaluator
        """
        
        self.requirements = requirements
        if thought_generator_examples:
            if os.path.isfile(thought_generator_examples) and thought_generator_examples.endswith('.examples'):
                with open(thought_generator_examples, 'r') as file:
                    self.thought_generator_examples = file.read()
            else:
                self.thought_generator_examples = thought_generator_examples
        else:
            self.thought_generator_examples = None
        if state_evaluator_examples:
            if os.path.isfile(state_evaluator_examples) and state_evaluator_examples.endswith('.examples'):
                with open(state_evaluator_examples, 'r') as file:
                    self.state_evaluator_examples = file.read()
            else:
                self.state_evaluator_examples = state_evaluator_examples
        else:
            self.state_evaluator_examples = None

        
    def set_input(self, query: str, qid: str="test"):
        """Set input parameters for the workflow
        Args:
            query: Input query content
            qid: Query ID
        """
        self.query = query
        self.qid = qid
        self._configure_tasks()
        self._configure_workflow()

    def _configure_tasks(self):
        """Configure task components in the workflow"""
        
        self.thought_decomposition_task = simple_task(
            task_def_name=ThoughtDecomposition,
            task_reference_name="thought_decomposition",
            inputs={
                "qid": self.qid,
                "requirements": self.requirements,
                "problem": self.query,
            }
        )
        self.thought_generator_task = simple_task(
            task_def_name=ThoughtGenerator, task_reference_name="thought_generator",
            inputs={
                "examples": self.thought_generator_examples,
            }
        )
        self.state_evaluator_task = simple_task(
            task_def_name=StateEvaluator, task_reference_name="state_evaluator",
            inputs={
                "examples": self.state_evaluator_examples,
            }
        )
        self.search_algorithm_task = simple_task(
            task_def_name=SearchAlgorithm, task_reference_name="search_algorithm"
        )
        
        self.tot_loop_task = DoWhileTask(
            task_ref_name='tot_loop', tasks=[self.thought_generator_task, self.state_evaluator_task, self.search_algorithm_task], 
            termination_condition='if ($.search_algorithm["finish"] == true){false;} else {true;} ')

    def _configure_workflow(self):
        """Configure the execution order of the workflow"""
        # self >> self.thought_decomposition_task >> self.thought_generator_task >> self.state_evaluator_task >> self.search_algorithm_task
        self >> self.thought_decomposition_task >> self.tot_loop_task
        self.result = self.search_algorithm_task.output("result")
        print(self.result)
        
        
        