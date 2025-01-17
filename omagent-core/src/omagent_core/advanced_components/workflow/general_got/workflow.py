from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.advanced_components.workflow.general_got.agent.splitter.splitter import TaskSplitter
from omagent_core.advanced_components.workflow.general_got.agent.generater.generater import TaskGenerater
from omagent_core.advanced_components.workflow.general_got.agent.score.score import TaskScore
from omagent_core.advanced_components.workflow.general_got.agent.keep_best_n.keep_best_n import KeepBestN
from omagent_core.advanced_components.workflow.general_got.agent.concluder.concluder import TaskConcluder
from omagent_core.advanced_components.workflow.general_got.agent.task_exit_monitor.task_exit_monitor import GoTTaskExitMonitor
from omagent_core.engine.workflow.task.do_while_task import DnCLoopTask



class GoTWorkflow(ConductorWorkflow):
    def __init__(self):
        super().__init__(name='got_sort_workflow')
        
    def set_input(self, query: str, task: str, meta: dict):
        self.query = query
        self.task = task
        self.meta = meta
        self._configure_tasks()
        self._configure_workflow()

    def _configure_tasks(self):
        self.splitter_task = simple_task(
            task_def_name=TaskSplitter,
            task_reference_name='task_splitter',
            inputs={'query': self.query, "task": self.task, "meta": self.meta}
        )

        self.generater_task = simple_task(
            task_def_name=TaskGenerater,
            task_reference_name='task_generater'
        )
        self.score_task = simple_task(
            task_def_name=TaskScore,
            task_reference_name='task_score'
        )

        self.keep_best_n_task = simple_task(
            task_def_name=KeepBestN,
            task_reference_name='task_keep_best_n'
        )


        self.got_task_exit_monitor = simple_task(
            task_def_name=GoTTaskExitMonitor,
            task_reference_name='got_task_exit_monitor'
        )


        self.got_loop_task = DnCLoopTask(
            task_ref_name='got_loop_task',
            tasks=[self.generater_task, self.score_task, self.keep_best_n_task],
            post_loop_exit=[self.got_task_exit_monitor]
        )

        self.concluder_task = simple_task(
            task_def_name=TaskConcluder,
            task_reference_name='task_concluder'
        )

    def _configure_workflow(self):
        self >> self.splitter_task >> self.got_loop_task >> self.concluder_task

