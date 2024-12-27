from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow



class SelfConsistentWorkflow(ConductorWorkflow):

    def __init__(self):


        
        
        super().__init__(
                name='self_consistent_workflow')
    
    def set_input(self,  user_question: str, path_num: int):
        self.user_question = user_question
        self.path_num = path_num
        self._configure_tasks()
        self._configure_workflow()

    def _configure_tasks(self):

        self.reasoning_task = simple_task(task_def_name='COTReasoning', task_reference_name='cot_reasoning', inputs={'user_question': self.user_question,'path_num':self.path_num})

        self.extract_task = simple_task(task_def_name='COTExtract', task_reference_name='cot_extract', inputs={'reasoning_result': self.reasoning_task.output('reasoning_result')})

        self.conclude_task = simple_task(task_def_name='COTConclusion', task_reference_name='cot_conclude', inputs={'final_answer': self.extract_task.output('final_answer'),"question":self.user_question})


    def _configure_workflow(self):
        
        self   >> self.reasoning_task  >>  self.extract_task >> self.conclude_task
        
    