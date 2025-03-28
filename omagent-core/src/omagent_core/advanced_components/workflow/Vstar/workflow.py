from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.do_while_task import DoWhileTask
from omagent_core.engine.workflow.task.switch_task import SwitchTask



class VstarWorkflow(ConductorWorkflow):

    def __init__(self):
        super().__init__(name='vstar_workflow')

    def set_input(self, query: str, image_path: str, qid: str='test',):
        self.qid = qid
        self.query = query
        self.image_path = image_path
        self._configure_tasks()
        self._configure_workflow()

    def _configure_tasks(self):
        
        self.vqa_llm_preprocess = simple_task(
            task_def_name='VQA_LLM_Preprocess', 
            task_reference_name='vqa_llm_preprocess',
            inputs={
                "qid": self.qid,
                "query": self.query,
                "image_path": self.image_path
            }
        )
        
        self.vqa_llm = simple_task(
            task_def_name='VQA_LLM', 
            task_reference_name='vqa_llm'
        )
        
        vstar_search_preprocess = simple_task(
            task_def_name='VstarSearchPreprocess', 
            task_reference_name='vstar_search_preprocess'
        )
        
        vstar_loop_check = simple_task(
            task_def_name='VstarLoopCheck',
            task_reference_name='vstar_loop_check'
        )
        
        vstar_search = simple_task(
            task_def_name='VstarSearch', 
            task_reference_name='vstar_search'
        )
        
        vstar_search_check = simple_task(
            task_def_name='VstarSearchCheck', 
            task_reference_name='vstar_search_check'
        )

        vstar_search_loop = DoWhileTask(
            task_ref_name='vstar_search_loop', 
            tasks=[vstar_search, vstar_search_check],
            termination_condition='if ($.vstar_search_check["finish"] == true){false;} else {true;}'
        )

        self.vstar_loop = DoWhileTask(
            task_ref_name='vstar_loop',
            tasks=[vstar_search_preprocess, vstar_search_loop, vstar_loop_check],
            termination_condition='if ($.vstar_loop_check["finish"] == true){false;} else {true;}'
        )


        self.vqa_llm_post = simple_task(
            task_def_name='VQA_LLM_Post', 
            task_reference_name='vqa_llm_post'
        )
        
        self.switch_task = SwitchTask(
            task_ref_name='switch_task',
            case_expression=self.vqa_llm.output("vqa_llm_succeed"),
        )
        self.switch_task.switch_case(0, [self.vstar_loop])
        # self.switch_task.switch_case(1, self.vqa_llm_post)

    def _configure_workflow(self):
        self >> self.vqa_llm_preprocess >> self.vqa_llm >> self.switch_task >> self.vqa_llm_post
        self.result = self.vqa_llm_post.output("result")
