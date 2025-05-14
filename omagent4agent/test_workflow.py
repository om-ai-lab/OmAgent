
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from agent.ExecuteAgent.ExecuteAgent import ExecuteAgent


class OmAgent4Agent(ConductorWorkflow): 
    def __init__(self):
        super().__init__(name="OmAgent4AgentTester")

    def set_input(self,  folder_path: str, example_inputs: str):        
        self.folder_path = folder_path
        self.example_inputs = example_inputs
        print ("folder_path",self.folder_path)
        print ("example_inputs",self.example_inputs)
        self._configure_tasks()
        self._configure_workflow()

    def _configure_tasks(self):

        self.execute_agent_task = simple_task(
            task_def_name=ExecuteAgent,
            task_reference_name="execute_agent",
            inputs={"folder_path": self.folder_path, "example_inputs": self.example_inputs}
        )


    def _configure_workflow(self):
        # configure workflow execution flow
        #self >> self.planner_task >> self.workflow_manager_task >> self.worker_manager_task >> self.worker_verifier_task
        #self >> self.planner_task >> self.workflow_loop_task >> self.worker_manager_task >> self.config_manager_task 
        self >> self.execute_agent_task 
        #self.dnc_structure = self.task_exit_monitor_task.output("dnc_structure")
        #self.last_output = self.task_exit_monitor_task.output("last_output")
