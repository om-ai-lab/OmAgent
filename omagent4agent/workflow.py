from agent.Planner.Planner import Planner
from agent.WorkflowVerifier.WorkflowVerifier import WorkflowVerifier
from agent.WorkflowManager.WorkflowManager import WorkflowManager
from agent.WorkerManager.WorkerManager import WorkerManager
from agent.WorkerVerifier.WorkerVerifier import WorkerVerifier

from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.do_while_task import DoWhileTask
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.engine.workflow.task.switch_task import SwitchTask
from agent.ConfigManager.ConfigManager import ConfigManager
from agent.ExecuteAgent.ExecuteAgent import ExecuteAgent
from agent.WorkerVerifier.RuleBasedVerifier import RuleBasedVerifier
from agent.WorkflowVerifier.WorkflowDebug import WorkflowDebug
from agent.DebugAgent.DebugAgent import DebugAgent


class OmAgent4Agent(ConductorWorkflow): 
    def __init__(self):
        super().__init__(name="OmAgent4Agent")

    def set_input(self,  initial_description: str):        
        self.initial_description = initial_description
        print ("initial_description",self.initial_description)
        self._configure_tasks()
        self._configure_workflow()

    def _configure_tasks(self):
        self.planner_task = simple_task(
            task_def_name=Planner,
            task_reference_name="planner",
            inputs={"initial_description": self.initial_description},
        )

        self.workflow_manager_task = simple_task(
            task_def_name=WorkflowManager,
            task_reference_name="workflow_manager",
        )
        self.workflow_verifier_task = simple_task(
            task_def_name=WorkflowVerifier,
            task_reference_name="workflow_verifier"
        )

        self.workflow_verifier_task2 = simple_task(
            task_def_name=WorkflowVerifier,
            task_reference_name="workflow_verifier2"
        )

        self.worker_verifier_task = simple_task(
            task_def_name=WorkerVerifier,
            task_reference_name="worker_verifier"
        )

        self.workflow_debug_task = simple_task(
            task_def_name=WorkflowDebug,
            task_reference_name="workflow_debug",
        )

        self.workflow_loop_task = DoWhileTask(
            task_ref_name="workflow_loop",
            tasks=[self.workflow_debug_task, self.workflow_verifier_task2],
            termination_condition='if ($.workflow_verifier2["switch_case_value"] == true){false;} else {true;} ',
        )

        self.workflow_verifier_switch_task = SwitchTask(
            task_ref_name="workflow_verifier_switch_task",
            case_expression=self.workflow_verifier_task.output("switch_case_value"),
        )

        self.workflow_verifier_switch_task.switch_case("false", self.workflow_loop_task)
   
        self.config_manager_task = simple_task(
            task_def_name=ConfigManager,
            task_reference_name="config_manager"
        )

        self.worker_manager_task = simple_task(
            task_def_name=WorkerManager,
            task_reference_name="worker_manager"
        )

        self.execute_agent_task = simple_task(
            task_def_name=ExecuteAgent,
            task_reference_name="execute_agent",
            inputs={"folder_path": None, "example_inputs": None}
        )
        self.rulebase_worker_verifier_task = simple_task(
            task_def_name=RuleBasedVerifier,
            task_reference_name="rulebase_worker_verifier"
        )

        self.execute_and_debug_task = simple_task(
            task_reference_name="execute_and_debug_task",
            task_def_name=DebugAgent,
            inputs={"folder_path": None, "example_inputs": None}
        )

        self.workflow_loop_task = DoWhileTask(
            task_ref_name="workflow_loop_for_debug",
            #tasks=[self.worker_manager_task, self.rulebase_worker_verifier_task, self.config_manager_task, self.execute_and_debug_task],
            tasks=[self.worker_manager_task, self.config_manager_task, self.execute_and_debug_task],
            termination_condition="if ($.execute_and_debug_task['finished'] == true){false;} else {true;} ",
            #termination_condition="if ($.execute_agent_task2['has_error'] == true){false;} else {true;} ",
        )

        """
        self.debug_task = simple_task(
            task_def_name=DebugAgent,
            task_reference_name="debug_task",
        )

        self.execute_agent_task2 = simple_task(
            task_def_name=ExecuteAgent,
            task_reference_name="execute_agent2",
            inputs={"folder_path": None, "example_inputs": None}
        )

        self.switch_task_for_debug = SwitchTask(
            task_ref_name="switch_task_for_debug",
            case_expression=self.execute_agent_task.output("has_error"),
        )

        self.debug_task2 = simple_task(
            task_def_name=DebugAgent,
            task_reference_name="debug_task2",
        )
        """

        #self.workflow_loop_task = DoWhileTask(
        #    task_ref_name="workflow_loop_for_debug",
        #    tasks=[self.debug_task, self.execute_agent_task2],
        #    termination_condition="if ($.debug_task['finished'] == true){false;} else {true;} ",
        #    #termination_condition="if ($.execute_agent_task2['has_error'] == true){false;} else {true;} ",
        #)

        #self.switch_task_for_debug.switch_case("true", self.workflow_loop_task)   



    def _configure_workflow(self):
        # configure workflow execution flow
        #self >> self.planner_task >> self.workflow_manager_task >> self.worker_manager_task >> self.worker_verifier_task
        #self >> self.planner_task >> self.workflow_manager_task >> self.workflow_verifier_task >> self.workflow_verifier_switch_task  >> self.worker_manager_task >> self.config_manager_task >> self.rulebase_worker_verifier_task >> self.execute_agent_task >> self.switch_task_for_debug
        self >> self.planner_task >> self.workflow_manager_task >> self.workflow_verifier_task >> self.workflow_verifier_switch_task  >> self.workflow_loop_task
        #self.dnc_structure = self.task_exit_monitor_task.output("dnc_structure")
        #self.last_output = self.task_exit_monitor_task.output("last_output")
