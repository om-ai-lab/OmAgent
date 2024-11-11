from omagent_core.engine.workflow.task.fork_task import ForkTask
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.utils.registry import registry


@registry.register_worker()
class SimpleWorker1(BaseWorker):
    def _run(self):
        print("worker1")
        return {}


@registry.register_worker()
class SimpleWorker2(BaseWorker):
    def _run(self):
        print("worker2")
        return {}


@registry.register_worker()
class SimpleWorker3(BaseWorker):
    def _run(self):
        print("worker3")
        return {}


# Create the main workflow
workflow = ConductorWorkflow(name="fork_join_test")

# Create tasks for parallel execution
task1 = simple_task(task_def_name="SimpleWorker1", task_reference_name="parallel_task1")
task2 = simple_task(task_def_name="SimpleWorker2", task_reference_name="parallel_task2")
task3 = simple_task(task_def_name="SimpleWorker3", task_reference_name="parallel_task3")

# Create parallel execution paths
path1 = [task1]  # First parallel path
path2 = [task2]  # Second parallel path
path3 = [task3]  # Third parallel path

# Create the fork task with multiple parallel paths
fork_task = ForkTask(
    task_ref_name="parallel_execution",
    forked_tasks=[path1, path2, path3],
    # The join will wait for the last task in each path
    join_on=["parallel_task1", "parallel_task2", "parallel_task3"]
)

# Add the fork task to the workflow
workflow.add(fork_task)

workflow.register(overwrite=True)