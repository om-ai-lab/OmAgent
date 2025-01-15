from omagent_core.advanced_components.workflow.dnc.agent.conqueror.conqueror import \
    TaskConqueror
from omagent_core.advanced_components.workflow.dnc.agent.construct_dnc_payload.construct_dnc_payload import \
    ConstructDncPayload
from omagent_core.advanced_components.workflow.dnc.agent.divider.divider import \
    TaskDivider
from omagent_core.advanced_components.workflow.dnc.agent.structure_update.structure_update import \
    StructureUpdate
from omagent_core.advanced_components.workflow.dnc.agent.task_exit_monitor.task_exit_monitor import \
    TaskExitMonitor
from omagent_core.advanced_components.workflow.dnc.agent.task_rescue.rescue import \
    TaskRescue
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.do_while_task import DnCLoopTask
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.engine.workflow.task.switch_task import SwitchTask


class DnCWorkflow(ConductorWorkflow):
    def __init__(self):
        super().__init__(name="dnc_workflow")

    def set_input(self, query: str):
        self.query = query
        self._configure_tasks()
        self._configure_workflow()

    def _configure_tasks(self):
        # construct input query into dnc tree structure
        self.construct_dnc_payload_task = simple_task(
            task_def_name=ConstructDncPayload,
            task_reference_name="construct_dnc_payload",
            inputs={"query": self.query},
        )

        # this task is to update dnc tree structure using stm
        self.structure_update_task = simple_task(
            task_def_name=StructureUpdate,
            task_reference_name="structure_update",
            inputs={
                "dnc_structure": self.construct_dnc_payload_task.output("dnc_structure")
            },
        )
        # conqueror task for task generation
        self.conqueror_task = simple_task(
            task_def_name=TaskConqueror,
            task_reference_name="task_conqueror",
            inputs={
                "dnc_structure": self.structure_update_task.output("dnc_structure"),
                "last_output": self.structure_update_task.output("last_output"),
            },
        )

        # divider task for task division
        self.divider_task = simple_task(
            task_def_name=TaskDivider,
            task_reference_name="task_divider",
            inputs={
                "dnc_structure": self.conqueror_task.output("dnc_structure"),
                "last_output": self.conqueror_task.output("last_output"),
            },
        )

        # rescue task for task rescue
        self.rescue_task = simple_task(
            task_def_name=TaskRescue,
            task_reference_name="task_rescue",
            inputs={
                "dnc_structure": self.conqueror_task.output("dnc_structure"),
                "last_output": self.conqueror_task.output("last_output"),
            },
        )

        # wwitch task for task routing
        self.switch_task = SwitchTask(
            task_ref_name="switch_task",
            case_expression=self.conqueror_task.output("switch_case_value"),
        )
        self.switch_task.switch_case("complex", self.divider_task)
        self.switch_task.switch_case("failed", self.rescue_task)

        # task exit monitor task for task exit monitoring
        self.task_exit_monitor_task = simple_task(
            task_def_name=TaskExitMonitor, task_reference_name="task_exit_monitor"
        )

        # DnC loop task for task loop
        self.dncloop_task = DnCLoopTask(
            task_ref_name="dncloop_task",
            tasks=[self.structure_update_task, self.conqueror_task, self.switch_task],
            post_loop_exit=[self.task_exit_monitor_task],
        )

    def _configure_workflow(self):
        # configure workflow execution flow
        self >> self.construct_dnc_payload_task >> self.dncloop_task
        self.dnc_structure = self.task_exit_monitor_task.output("dnc_structure")
        self.last_output = self.task_exit_monitor_task.output("last_output")
