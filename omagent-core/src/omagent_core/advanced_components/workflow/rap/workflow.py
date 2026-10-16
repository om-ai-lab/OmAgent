from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.engine.workflow.task.do_while_task import DoWhileTask
from .agent.selection.selection import Selection
from .agent.expansion.expansion import Expansion
from .agent.simulation_preprocess.simulation_preprocess import SimulationPreProcess
from .agent.simulation_postprocess.simulation_postprocess import SimulationPostProcess
from .agent.back_propagation.back_propagation import BackPropagation
from .agent.mcts_completion_check.mcts_completion_check import MCTSCompletionCheck
from .agent.output_interface.output_interface import OutputInterface

class RAPWorkflow(ConductorWorkflow):
    def __init__(self):
        super().__init__(name="rap_workflow")

    def set_input(self, query: str,
                    depth_limit: int = 3, sub_question_gen_num: int = 3, yes_sample_num: int = 10, answer_gen_num: int = 5,
                    mcts_iter_num: int = 1, n_shot: int = 4):
        self.query = query
        self.depth_limit = depth_limit
        self.sub_question_gen_num = sub_question_gen_num
        self.yes_sample_num = yes_sample_num
        self.answer_gen_num = answer_gen_num
        self.mcts_iter_num = mcts_iter_num
        self.n_shot = n_shot
        self._configure_tasks()
        self._configure_workflow()

    def _configure_tasks(self):
        # Selection task
        self.selection_task = simple_task(
            task_def_name='Selection',
            task_reference_name='selection',
            inputs={"depth_limit": self.depth_limit}
        )

        # Expansion task
        self.expansion_task = simple_task(
            task_def_name='Expansion',
            task_reference_name='expansion',
            inputs={"n_shot": self.n_shot, "sub_question_gen_num": self.sub_question_gen_num, "yes_sample_num": self.yes_sample_num, "answer_gen_num": self.answer_gen_num}
        )

        # Simulation pre-process task
        self.simulation_preprocess_task = simple_task(
            task_def_name='SimulationPreProcess',
            task_reference_name='simulation_preprocess'
        )

        # Simulation expansion task
        self.expansion2_task = simple_task(
            task_def_name='Expansion',
            task_reference_name='expansion2',
            inputs={"n_shot": self.n_shot, "sub_question_gen_num": self.sub_question_gen_num, "yes_sample_num": self.yes_sample_num, "answer_gen_num": self.answer_gen_num}
        )

        # Simulation post-process task
        self.simulation_postprocess_task = simple_task(
            task_def_name='SimulationPostProcess',
            task_reference_name='simulation_postprocess',
            inputs={"depth_limit": self.depth_limit}
        )

        # Back propagation task
        self.back_propagation_task = simple_task(
            task_def_name='BackPropagation',
            task_reference_name='back_propagation'
        )

        # MCTS completion check task
        self.mcts_completion_check_task = simple_task(
            task_def_name='MCTSCompletionCheck',
            task_reference_name='mcts_completion_check',
            inputs={"mcts_iter_num": self.mcts_iter_num}
        )

        # Output interface task
        self.output_interface_task = simple_task(
            task_def_name='OutputInterface',
            task_reference_name='output_interface'
        )

        # Configure simulation loop
        self.simulation_loop = DoWhileTask(
            task_ref_name='simulation_loop',
            tasks=[self.expansion2_task, self.simulation_postprocess_task],
            termination_condition='if ($.simulation_postprocess["finish"] == true){false;} else {true;}'
        )

        # Configure MCTS loop
        self.mcts_loop = DoWhileTask(
            task_ref_name='mcts_loop',
            tasks=[
                self.selection_task,
                self.expansion_task,
                self.simulation_preprocess_task,
                self.simulation_loop,
                self.back_propagation_task,
                self.mcts_completion_check_task
            ],
            termination_condition='if ($.mcts_completion_check["finish"] == true){false;} else {true;}'
        )

    def _configure_workflow(self):
        # Configure workflow execution flow
        self >> self.mcts_loop >> self.output_interface_task
        
        # Set outputs
        self.final_answer = self.output_interface_task.output("final_answer") 