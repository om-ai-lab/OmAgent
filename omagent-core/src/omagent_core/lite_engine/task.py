from pathlib import Path
from typing import List, Callable


CURRENT_PATH = Path(__file__).parents[0]


class Task: 
    def __init__(self, name, func: Callable = None, *args, **kwargs):
        self.name = name
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.next_tasks: List['Task'] = []
        self.result = None
        self._parent_task = None

    def execute(self):
        print(f"Executing {self.name}")
        # Evaluate args and kwargs if they are callables
        evaluated_args = [arg() if callable(arg) else arg for arg in self.args]
        evaluated_kwargs = {k: v() if callable(v) else v for k, v in self.kwargs.items()}

        # Only execute if a function is provided
        if self.func is not None:
            self.result = self.func(*evaluated_args, **evaluated_kwargs)

        # Execute subsequent tasks
        for task in self.next_tasks:
            task.execute()
        return self.result
    
    def output(self):
        return self.result
    """
    def __rshift__(self, task_or_dict):
        # If other is a dictionary, treat it as a switch condition
        if isinstance(task_or_dict, dict):
            switch_task = SwitchTask(name=f"{self.name}_switch", cases=task_or_dict)
            self.next_tasks.append(switch_task)
            setattr(switch_task, '_parent_task', self)
            return switch_task
        else:
            self.next_tasks.append(task_or_dict)
            if isinstance(task_or_dict, Task):
                setattr(task_or_dict, '_parent_task', self)
            return task_or_dict
    """

class SwitchTask(Task):
    def __init__(self, name, cases: dict):
        super().__init__(name=name)
        self.cases = cases
        self.default_task = None

    def execute(self):
        print(f"Executing switch: {self.name}")
        parent = getattr(self, '_parent_task', None)
        if parent is None:
            print("No parent found for switch, cannot determine branch.")
            # Still proceed to next tasks even if no parent
            for task in self.next_tasks:
                task.execute()
            return None

        parent_result = parent.output()
        chosen_task = None
        if isinstance(parent_result, dict) and 'switch_case_value' in parent_result:
            case_value = parent_result['switch_case_value']
            chosen_task = self.cases.get(case_value, None)
            if chosen_task is None:
                print(f"No matching case found for '{case_value}', skipping branch.")
        else:
            print("No valid switch_case_value in parent output, skipping branch.")

        if chosen_task:
            chosen_task.execute()

        # Run next_tasks even if no case matched
        for task in self.next_tasks:
            task.execute()
        return None
    """
    def __rshift__(self, other):
        self.next_tasks.append(other)
        if isinstance(other, Task):
            setattr(other, '_parent_task', self)
        return other
    """

class DoWhileTask(Task):
    def __init__(self, name, tasks: List[Task], termination_condition: str):
        super().__init__(name=name)
        # The tasks to be executed in the loop body
        self.loop_tasks = tasks
        for t in self.loop_tasks:
            setattr(t, '_parent_task', self)
        self.termination_condition_str = termination_condition
        self.results_by_name = {}

    def execute(self):
        print(f"Executing do-while loop: {self.name}")
        # This is a do-while: execute first, then check condition
        while True:
            # Run all loop tasks once
            for t in self.loop_tasks:
                t.execute()
                self.results_by_name[t.name] = t.output()

            condition = self._evaluate_condition()

            if not condition:
                break

        # After we exit the loop, run next tasks
        for task in self.next_tasks:
            task.execute()
        return None

    def _evaluate_condition(self):
        # Extract task3 decision
        task3_decision = self.results_by_name.get("task3", {}).get("decision", False)
        
        if task3_decision is True:
            return False
        else:
            return True

