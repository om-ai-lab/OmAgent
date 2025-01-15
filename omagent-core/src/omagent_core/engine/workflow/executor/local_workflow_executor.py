import uuid
from typing import Dict
import logging
from omagent_core.utils.registry import registry
import uuid
import logging
from omagent_core.engine.http.models import *
import json


class LocalWorkflowExecutor:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.workers = {}
        self.task_outputs = {}
        self.workflow_variables = {}
        
    def evaluate_input_parameters(self, task: Dict) -> Dict:
        processed_inputs = {}
        input_params = task.get('inputParameters') or task.get('input_parameters', {})

        for key, value in input_params.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):

                ref_path = value[2:-1]
                parts = ref_path.split('.')
                
                if parts[0] in self.task_outputs:
                    task_output = self.task_outputs[parts[0]]['output']
                    for part in parts[2:]:  
                        if isinstance(task_output, dict):
                            task_output = task_output.get(part, {})
                    processed_inputs[key] = task_output
            else:
                processed_inputs[key] = value
        return processed_inputs


    def start_workflow(self, workflow_def, start_request, workers) -> str:
        workflow_id = str(uuid.uuid4())        
        print ("start_request:", start_request.input)
        for i, task_def in enumerate(workflow_def.tasks):
            if i == 0:
                task_def.input_parameters = start_request.input
            self.execute_task(task_def.to_dict(), workers)

        #return workflow_id
    def worker_task(self, worker, *args, **kwargs):
        """Run the worker and put its output in the queue."""
        result = worker._run(*args, **kwargs)
        self.worker_output_queue.put(result)

    def execute_task(self, task: Dict, workers) -> Dict:
        """Execute a single task"""
        task_name = task['name']
        task_type = task['type']
        
        if task_type == 'SIMPLE':
            worker = workers[task_name]
            """
            if not worker_class:
                raise ValueError(f"Worker {task_name} not found")
            
            worker = worker_class()            
            """
            inputs = self.evaluate_input_parameters(task)            
            # Execute task
            result = worker._run(**inputs)
            # Store output
            task_ref_key = 'taskReferenceName' if 'taskReferenceName' in task else 'task_reference_name'

            self.task_outputs[task[task_ref_key]] = {
                'output': result
            }            
            return result
            
        elif task_type == 'DO_WHILE':
            while True:
                # Execute all tasks in loop
                for loop_task in task['loopOver' if 'loopOver' in task else 'loop_over']:                    
                    self.execute_task(loop_task, workers)
                if 'loopCondition' in task or "loop_condition" in task:
                    should_continue = not self.evaluate_loop_condition(task['loopCondition' if 'loopCondition' in task else "loop_condition"])            
                    if not should_continue:
                        break
                else:
                    exit_monitor_output = self.task_outputs['task_exit_monitor']['output']
                    if exit_monitor_output.get('exit_flag', False):
                        break
                    
        elif task_type == 'SWITCH':
            case_value = self.evaluate_input_parameters(task)['switchCaseValue']
            if case_value in task['decision_cases']:
                for case_task in task['decision_cases'][case_value]:
                    self.execute_task(case_task.to_dict(), workers)
            else:
                for default_task in task.get('defaultCase' if 'defaultCase' in task else 'default_case', []):
                    self.execute_task(default_task.to_dict(), workers)
                    
        return {}

    def evaluate_loop_condition(self, condition: str) -> bool:
        """Evaluate loop condition using the task outputs"""
        # Clean up the condition string
        condition = condition.strip()
        if condition.startswith('if'):
            condition = condition[2:].strip()
        
        # Extract the main condition part (between parentheses)
        main_condition = condition[condition.find('(') + 1:condition.rfind(')')].strip()
        
        # First split by OR operator (||)
        or_conditions = [cond.strip() for cond in main_condition.split('||')]
        
        for or_part in or_conditions:
            # For each OR part, split by AND operator (&&)
            and_conditions = [cond.strip() for cond in or_part.split('&&')]
            
            # All AND conditions must be true for this OR part to be true
            and_results = True
            for and_condition in and_conditions:
                condition_result = self._evaluate_single_condition(and_condition)
                if not condition_result:
                    and_results = False
                    break
            
            # If any OR part (all of its AND conditions) is true, return false to stop the loop
            if and_results:
                return False
        
        # If no OR conditions were true (meaning no AND group was completely true)
        # return true to continue the loop
        return True

    def _evaluate_single_condition(self, condition: str) -> bool:
        """Evaluate a single condition without OR operators"""
        condition = condition.strip('()')
        
        if '$.' not in condition:
            return False
            
        # Handle different comparison operators
        if '==' in condition:
            left, right = [part.strip() for part in condition.split('==')]
        elif '>' in condition:
            left, right = [part.strip() for part in condition.split('>')]
            operator = '>'
        else:
            return False
            
        # Parse left side (task reference)
        if left.startswith('$.'):
            task_ref = left[2:].split('.')[0]
            properties = left[2:].split('.')[1:]
            
            # Get task output and navigate through properties
            value = self.task_outputs.get(task_ref, {}).get('output', {})
            for prop in properties:
                if isinstance(value, dict):
                    value = value.get(prop)
                else:
                    return False
                    
            # Parse right side (could be another task reference or a literal)
            if right.startswith('$.'):
                task_ref = right[2:].split('.')[0]
                properties = right[2:].split('.')[1:]
                right_value = self.task_outputs.get(task_ref, {}).get('output', {})
                for prop in properties:
                    if isinstance(right_value, dict):
                        right_value = right_value.get(prop)
                    else:
                        return False
            else:
                # Handle literals
                if right.lower() == 'true':
                    right_value = True
                elif right.lower() == 'false':
                    right_value = False
                else:
                    try:
                        right_value = int(right)
                    except ValueError:
                        right_value = right
                        
            # Compare values
            if operator == '>':
                return value > right_value
            else:
                return value == right_value
                
        return False


class WorkflowExecutor:
    def __init__(self):
        self.local_executor = LocalWorkflowExecutor()    

    def start_workflow(self, start_workflow_request: StartWorkflowRequest, workers=None) -> str:
        return self.local_executor.start_workflow(
            workflow_def=start_workflow_request.workflow_def,
            start_request=start_workflow_request, workers=workers
        )

    def get_workflow(self, workflow_id: str, include_tasks: bool = None) -> Workflow:
        pass
    

    def terminate(self, workflow_id: str, reason: str = None):
        pass

    def register_workflow(self, workflow: WorkflowDef, overwrite: bool = None) -> object:
        """Create a new workflow definition"""
        with open(f'{workflow.to_dict()["name"]}.json', 'w') as file:
            json.dump(workflow.toJSON(), file, indent=4)        

    def __del__(self):
        pass