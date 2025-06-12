
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from agent.ExecuteAgent.ExecuteAgent import ExecuteAgent
from agent.DebugAgent.DebugAgent import DebugAgent
from agent.TaskExitMonitor.TaskExitMonitor import TaskExitMonitor_a4a
from omagent_core.engine.workflow.task.do_while_task import DoWhileTask
from omagent_core.engine.workflow.task.switch_task import SwitchTask


class OmAgent4Agent(ConductorWorkflow): 
    def __init__(self):
        super().__init__(name="OmAgent4AgentDebug")

    def set_input(self,  folder_path: str, example_inputs: str):        
        self.folder_path = folder_path
        self.example_inputs = example_inputs
        self._configure_tasks()
        self._configure_workflow()

    def _configure_tasks(self):
        """    
        self.execute_agent_task = simple_task(
            task_def_name=ExecuteAgent,
            task_reference_name="execute_agent",
            inputs={"folder_path": self.folder_path, "example_inputs": self.example_inputs}
        )
        """

        self.debug_task = simple_task(
            task_def_name=DebugAgent,
            task_reference_name="debug",
            inputs={"folder_path": self.folder_path, "example_inputs": self.example_inputs}
        )

        self.execute_agent_task2 = simple_task(
            task_def_name=ExecuteAgent,
            task_reference_name="execute_agent2",
            inputs={"folder_path": self.folder_path, "example_inputs": self.example_inputs}
        )

        self.switch_task = SwitchTask(
            task_ref_name="switch_task",
            case_expression=self.execute_agent_task2.output("has_error"),
        )
        """
        self.workflow_loop_task = DoWhileTask(
            task_ref_name="workflow_loop",
            tasks=[self.debug_task, self.execute_agent_task2],
            termination_condition="if ($.debug['finished'] == true){false;} else {true;} ",
            #termination_condition="if ($.execute_agent_task2['has_error'] == true){false;} else {true;} ",
        )
        """

        #self.switch_task.switch_case("true", self.workflow_loop_task)   

        self.workflow_loop_task2 = DoWhileTask(
            task_ref_name="workflow_loop2",
            tasks=[self.execute_agent_task2, self.debug_task],
            termination_condition="if ($.execute_agent_task2['has_error'] == true){false;} else {true;} ",
            #termination_condition="if ($.execute_agent_task2['has_error'] == true){false;} else {true;} ",
        )

        self.task_exit_monitor_task = simple_task(
            task_def_name=TaskExitMonitor_a4a, task_reference_name="task_exit_monitor"
        )


    def _configure_workflow(self):
        # configure workflow execution flow
        #self >> self.planner_task >> self.workflow_manager_task >> self.worker_manager_task >> self.worker_verifier_task
        #self >> self.planner_task >> self.workflow_loop_task >> self.worker_manager_task >> self.config_manager_task 
        self >> self.debug_task   
        #self >> self.execute_agent_task
        #self.dnc_structure = self.task_exit_monitor_task.output("dnc_structure")
        #self.last_output = self.task_exit_monitor_task.output("last_output")
