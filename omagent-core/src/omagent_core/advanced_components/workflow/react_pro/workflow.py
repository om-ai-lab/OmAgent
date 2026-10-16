from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.engine.workflow.task.do_while_task import DoWhileTask
from .agent.action.action import Action
from .agent.think.think import Think
from omagent_core.advanced_components.workflow.react.agent.wiki_search.wiki_search import WikiSearch
from omagent_core.advanced_components.workflow.react.agent.react_output.react_output import ReactOutput

class ReactProWorkflow(ConductorWorkflow):
    def __init__(self):
        super().__init__(name='react_pro')
        
    def set_input(self, query: str, id: str = ""):
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
                'id': self.id
            }
        )
        
        # Action task
        self.action_task = simple_task(
            task_def_name=Action,
            task_reference_name='action'
        )
        
        # Wiki Search task
        self.wiki_search_task = simple_task(
            task_def_name=WikiSearch,
            task_reference_name='wiki_search',
            inputs={
                'action_output': self.action_task.output('output')
            }
        )
        
        # Do-While loop with max_turns from config
        self.loop_task = DoWhileTask(
            task_ref_name='react_pro_loop',
            tasks=[self.think_task, self.action_task, self.wiki_search_task], #'$.action[is_final] == true' 
            #(($.action.is_final == true) || ($.think.step_number > $.think.max_steps))
            termination_condition='(($.action.is_final == true) || ($.think.step_number > $.think.max_steps))' 
        )
        
        # Configure output task
        self.react_output_task = simple_task(
            task_def_name=ReactOutput,
            task_reference_name='react_output',
            inputs={
                'action_output': '${action.output}'
            }
        )
        
    def _configure_workflow(self):
        # Configure workflow execution sequence
        self >> self.loop_task >> self.react_output_task
