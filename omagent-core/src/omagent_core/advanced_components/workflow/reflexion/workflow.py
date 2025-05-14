from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.engine.workflow.task.do_while_task import DoWhileTask
from omagent_core.advanced_components.workflow.react_pro.agent.action.action import Action
from omagent_core.advanced_components.workflow.react_pro.agent.think.think import Think
from omagent_core.advanced_components.workflow.react.agent.wiki_search.wiki_search import WikiSearch
from omagent_core.advanced_components.workflow.react.agent.react_output.react_output import ReactOutput
from .agent.reflect.reflect import Reflect

class ReflexionWorkflow(ConductorWorkflow):
    def __init__(self):
        super().__init__(name='reflexion')
        
    def set_input(self, query: str,id: str = ""):
        self.query = query
        self.id = id
        self._configure_tasks()
        self._configure_workflow()
        
    def _configure_tasks(self):
        # Think task
        self.think_task = simple_task(
            task_def_name=Think,                
            task_reference_name='think',
            inputs={
                'query': self.query,
            }
        )
        
        # Action task
        self.action_task = simple_task(
            task_def_name=Action,
            task_reference_name='action',
        )
        
        # Wiki Search task
        self.wiki_search_task = simple_task(
            task_def_name=WikiSearch,
            task_reference_name='wiki_search',
            inputs={
                'action_output': self.action_task.output('output')
            }
        )
        
        # React output task
        self.react_output_task = simple_task(
            task_def_name=ReactOutput,
            task_reference_name='react_output',
            inputs={
                'action_output': '${action.output}'
            }
        )

        # Reflect task
        self.reflect_task = simple_task(
            task_def_name=Reflect,
            task_reference_name='reflect',
            inputs={
                'react_output': self.react_output_task.output('output'),
            }
        )
        
        # Do-While loop for React process
        self.react_loop_task = DoWhileTask(
            task_ref_name='react_pro_loop',
            tasks=[self.think_task, self.action_task, self.wiki_search_task],
            termination_condition='(($.action.is_final == true) || ($.think.step_number > $.think.max_steps))' 
        )

        # Outer Do-While loop for the entire process
        self.outer_loop_task = DoWhileTask(
            task_ref_name='outer_loop',
            tasks=[self.react_loop_task, self.react_output_task, self.reflect_task],
            termination_condition='(($.reflect.should_retry == false))'
        )

        # Final output task
        self.final_output_task = simple_task(
            task_def_name=ReactOutput,
            task_reference_name='final_output',
            inputs={
                'action_output': '${react_output.output}'
            }
        )
        
    def _configure_workflow(self):
        # Configure workflow execution sequence:
        # 1. Outer loop containing:
        #    a. React loop (think -> action -> wiki_search)
        #    b. React output
        #    c. Switch to reflect based on is_final
        # 2. Final output
        self >> self.outer_loop_task >> self.final_output_task 