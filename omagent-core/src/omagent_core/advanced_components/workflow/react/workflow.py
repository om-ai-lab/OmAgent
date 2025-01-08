from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.engine.workflow.task.do_while_task import DoWhileTask
from .agent.think_action.think_action import ThinkAction
from .agent.wiki_search.wiki_search import WikiSearch
from .agent.react_output.react_output import ReactOutput

class ReactWorkflow(ConductorWorkflow):
    def __init__(self):
        super().__init__(name='react_workflow')
        
    def set_input(self, query: str, id: str = "", max_turns: int = 8, example: str = ""):
        self.query = query
        self.id = id
        self.max_turns = max_turns
        self.example = example
        self._configure_tasks()
        self._configure_workflow()
        
    def _configure_tasks(self):
        # Combined Think and Action task
        self.think_action_task = simple_task(
            task_def_name=ThinkAction,
            task_reference_name='think_action',
            inputs={
                'query': self.query,
                'id': self.id,
                'example': self.example
            }
        )
        
        # Wiki Search task
        self.wiki_search_task = simple_task(
            task_def_name=WikiSearch,
            task_reference_name='wiki_search',
            inputs={
                'action_output': self.think_action_task.output('action'),
            }
        )
        
        # Do-While loop with max_turns from config
        self.loop_task = DoWhileTask(
            task_ref_name='react_loop',
            tasks=[self.think_action_task, self.wiki_search_task],
            inputs={'max_turns': self.max_turns},
            termination_condition=f'''
                if ($.think_action.is_final == true) {{
                    false;  // Stop loop if it's a Finish action
                }} else if ($.think_action.step_number > $.max_turns) {{
                    false;  // Stop loop if exceeded max turns
                }} else {{
                    true;   // Continue loop otherwise
                }}
            '''
        )
        
        # Output task
        self.react_output_task = simple_task(
            task_def_name=ReactOutput,
            task_reference_name='react_output',
            inputs={
                'action_output': '${think_action.output}',
                'workflow_id': '${workflow.workflowId}'
            }
        )
        
    def _configure_workflow(self):
        # Configure workflow execution sequence
        self >> self.loop_task >> self.react_output_task 