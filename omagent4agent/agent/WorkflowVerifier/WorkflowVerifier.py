
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
import json

@registry.register_worker()
class WorkflowVerifier(BaseWorker):    
    def _run(self, *args, **kwargs):          
        # Check for SWITCH task type
        workflow_json = self.stm(self.workflow_instance_id)["workflow_json"]
        try:
            workflow_json = json.loads(workflow_json)
        except:
            self.callback.info(message="Invalid JSON:"+str(workflow_json), agent_id=self.workflow_instance_id, progress="WorkflowVerifier")            
            self.stm(self.workflow_instance_id)["workflow_error_msg"] = "Invalid JSON. Json parsing error"            
            return {"switch_case_value": False, "error": "Invalid JSON"}

        for task in workflow_json.get('tasks', []):
            if task['type'] == 'SWITCH':
                if not task.get('inputParameters'):
                    self.callback.info(message=f"Error: SWITCH task '{task['name']}' has empty inputParameters.", agent_id=self.workflow_instance_id, progress="WorkflowVerifier")
                    self.stm(self.workflow_instance_id)["workflow_error_msg"] = "SWITCH task has empty inputParameters"
                    return {"switch_case_value": False, "error": "SWITCH task has empty inputParameters"}

        # Check for DO_WHILE task type
        for task in workflow_json.get('tasks', []):
            if task['type'] == 'DO_WHILE':
                loop_condition = task.get('loopCondition')
                loop_over = task.get('loopOver', [])
                if not loop_condition or not loop_over:
                    self.callback.info(message=f"Error: DO_WHILE task '{task['name']}' is missing loopCondition or loopOver.", agent_id=self.workflow_instance_id, progress="WorkflowVerifier")
                    self.stm(self.workflow_instance_id)["workflow_error_msg"] = "DO_WHILE task is missing loopCondition or loopOver"
                    return {"switch_case_value": False, "error": "DO_WHILE task is missing loopCondition or loopOver"}
                # Extract taskReferenceName from loopCondition
                try:
                    task_ref_name = loop_condition.split('$.')[1].split('.')[0].split('[')[0]
                except:
                    self.callback.info(message=f"Error: DO_WHILE task '{task['name']}' has invalid loopCondition grammar.", agent_id=self.workflow_instance_id, progress="WorkflowVerifier")
                    self.stm(self.workflow_instance_id)["workflow_error_msg"] = "DO_WHILE task has invalid loopCondition grammar"
                    return {"switch_case_value": False, "error": "DO_WHILE task has invalid loopCondition grammar"}
                print ("task_ref_name",task_ref_name)
                if not any(t['taskReferenceName'] == task_ref_name for t in loop_over):
                    self.callback.info(message=f"Error: taskReferenceName '{task_ref_name}' in loopCondition is not in loopOver for task '{task['name']}'.", agent_id=self.workflow_instance_id, progress="WorkflowVerifier")
                    self.stm(self.workflow_instance_id)["workflow_error_msg"] = "taskReferenceName in loopCondition is not in loopOver"
                    return {"switch_case_value": False, "error": "taskReferenceName in loopCondition is not in loopOver"}

        
        
        first_task = workflow_json["tasks"][0]        
        if first_task["inputParameters"] == {}:
            self.callback.info(message=f"Error: First task '{first_task['name']}' has empty inputParameters.", agent_id=self.workflow_instance_id, progress="WorkflowVerifier")
            self.stm(self.workflow_instance_id)["workflow_error_msg"] = "First task has empty inputParameters"
            return {"switch_case_value": False, "error": "First task has empty inputParameters"}

        for v in first_task["inputParameters"].values():
            if not "${workflow.input." in v:
                self.callback.info(message=f"Error: The input parameters are not correct. {v} is not in the workflow.input.", agent_id=self.workflow_instance_id, progress="WorkflowVerifier")
                self.stm(self.workflow_instance_id)["workflow_error_msg"] = "The input parameters are not correct. " + v + " is not in the workflow.input."
                return {"switch_case_value": False, "error": "The input parameters are not correct. " + v + " is not in the workflow.input."}
        self.callback.info(message="Workflow is valid", agent_id=self.workflow_instance_id, progress="WorkflowVerifier")
        self.stm(self.workflow_instance_id)["workflow_error_msg"] = "Workflow is valid"
        return {"switch_case_value": True}