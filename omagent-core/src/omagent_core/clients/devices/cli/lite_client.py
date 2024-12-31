from pathlib import Path
from omagent_core.services.connectors.redis import RedisConnector
from omagent_core.utils.container import container
container.register_connector(name='redis_stream_client', connector=RedisConnector)
from omagent_core.engine.orkes.orkes_workflow_client import workflow_client
from omagent_core.engine.http.models.workflow_status import terminal_status
#from omagent_core.lite_engine.workflow import LocalWorkflow
from omagent_core.utils.build import build_from_file
from omagent_core.engine.automator.task_handler import TaskHandler
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.http.models.workflow_status import running_status
from omagent_core.engine.automator.task_handler import TaskHandler
from omagent_core.utils.build import build_from_file
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.app.input import AppInput
from omagent_core.clients.devices.cli.callback import DefaultCallback
import yaml
from time import sleep
from urllib.parse import urlparse
import json
import os
from colorama import Fore, Style
from omagent_core.utils.container import container
from omagent_core.utils.logger import logging
from omagent_core.lite_engine.task import Task
from omagent_core.engine.worker.base import BaseWorker
import random
registry.import_module()
from typing import Dict, Any
import json
from pathlib import Path
import threading
import queue
import redis 


class LiteClient:
    def __init__(self, config_path, workflow_json):
        self._config_path = config_path
        self.tasks = {}
        self.workflow_data = {}
        self.current_task_index = 0
        self.workers = {}
        self.worker_output_queue = queue.Queue() 
        self.initialize_workflow(workflow_json)
        container.get_connector('redis_stream_client')._client.flushdb()


    def register_worker(self, worker_name: str, worker_class: Any):
        self.tasks[worker_name] = worker_class
        
    def initialize_workflow(self, workflow_json: Dict):
        self.workflow_data = json.load(open(workflow_json+".json"))
        self.task_outputs = {}
        self.workflow_variables = {}
        
    def evaluate_input_parameters(self, task: Dict) -> Dict:
        processed_inputs = {}
        
        for key, value in task.get('inputParameters', {}).items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                # Extract reference path
                ref_path = value[2:-1]
                parts = ref_path.split('.')
                
                # Get referenced task output
                if parts[0] in self.task_outputs:
                    task_output = self.task_outputs[parts[0]]['output']
                    for part in parts[2:]:  # Skip task name and 'output'
                        if isinstance(task_output, dict):
                            task_output = task_output.get(part, {})
                    processed_inputs[key] = task_output
            else:
                processed_inputs[key] = value
                
        return processed_inputs
    
    def worker_task(self, worker, *args, **kwargs):
        """Run the worker and put its output in the queue."""
        result = worker._run(*args, **kwargs)
        self.worker_output_queue.put(result)

    def execute_task(self, task: Dict) -> Dict:
        """Execute a single task"""
        task_name = task['name']
        task_type = task['type']
        
        if task_type == 'SIMPLE':

            worker_class = self.workers[task_name]
            if not worker_class:
                raise ValueError(f"Worker {task_name} not found")
            
            worker = worker_class            

            if task["name"]=='InputInterface':
                import threading
                workflow_thread = threading.Thread(
                target=self.worker_task,  # Call the method that adds the output to the queue
                args=(worker,),
                daemon=True
            )
                workflow_thread.start()

                # Handle user input in the main thread
                self.handle_user_input("Please input your question:")

                # Wait for the worker thread to complete
                workflow_thread.join()

                # Get the result from the queue
                if not self.worker_output_queue.empty():
                    worker_output = self.worker_output_queue.get()
                    self.task_outputs[task['taskReferenceName']] = {
                        'output': worker_output
                    }    
                    return worker_output
                    
                                #result = worker._run()
            else:
                inputs = self.evaluate_input_parameters(task)            
                print ("inputs:", inputs)            
                # Execute task
                result = worker._run(**inputs)
                # Store output
                self.task_outputs[task['taskReferenceName']] = {
                    'output': result
                }            
                return result
            
        elif task_type == 'DO_WHILE':
            while True:
                # Execute all tasks in loop
                for loop_task in task['loopOver']:
                    
                    self.execute_task(loop_task)
                exit_monitor_output = self.task_outputs['task_exit_monitor']['output']
                if exit_monitor_output.get('exit_flag', False):
                    break
                    
        elif task_type == 'SWITCH':
            # Get switch case value
            case_value = self.evaluate_input_parameters(task)['switchCaseValue']
            # Execute matching case
            if case_value in task['decisionCases']:
                for case_task in task['decisionCases'][case_value]:
                    self.execute_task(case_task)
            else:
                for default_task in task.get('defaultCase', []):
                    self.execute_task(default_task)
                    
        return {}
    
    def is_url(self, string: str) -> bool:
        """Check if string is a URL"""
        try:
            result = urlparse(string)
            return all([result.scheme, result.netloc])
        except:
            return False

    def is_file(self, path: str) -> bool:
        """Check if path is a valid file"""
        return os.path.isfile(path)

    def execute_workflow(self):
        """Execute the full workflow"""
        print (self.workflow_data)
        for task in self.workflow_data['tasks']:            
            self.execute_task(task)
    
    def process_message(self, message):
        logging.info(f"Received message: {message}")
        try:
            payload = message.get("payload")
            # check payload data
            if not payload:
                logging.error("Payload is empty")
                return False, None

            try:
                payload_data = json.loads(payload)
            except json.JSONDecodeError as e:
                logging.error(f"Payload is not a valid JSON: {e}")
                return False, None
            
            if "interaction_type" in payload_data and payload_data["interaction_type"] == 1:
                content = payload_data["message"]["content"]
                return True, content
                
        except Exception as e:
            logging.error(f"Error processing message: {e}")
            return False, None
        return False, None  

    def handle_user_input(self, prompt: str) -> Dict:
        """Handle interactive user input"""
        workflow_instance_id = "omagent_lite_ver"
        stream_name = f"{workflow_instance_id}_output"
        consumer_name = f"{workflow_instance_id}_agent"  # consumer name
        group_name = "omappagent"  # replace with your consumer group name
        poll_interval = 1
        sleep(poll_interval)
        #if self._input_prompt:
        #    self.first_input(workflow_instance_id=workflow_instance_id, input_prompt=self._input_prompt)
        try:
            container.get_connector('redis_stream_client')._client.xgroup_create(
                stream_name, group_name, id="0", mkstream=True
            )
            print (stream_name, group_name)
        except Exception as e:
            logging.debug(f"Consumer group may already exist: {e}")

        #while True:
        
            contents = []
            data_flag = False
            # read new messages from consumer group
            messages = container.get_connector('redis_stream_client')._client.xreadgroup(
                group_name, consumer_name, {stream_name: ">"}, count=1
            )
            # Convert byte data to string
            messages = [
                (stream, [(message_id, {k.decode('utf-8'): v.decode('utf-8') for k, v in message.items()}) for message_id, message in message_list])
                for stream, message_list in messages
            ]
            for stream, message_list in messages:
                for message_id, message in message_list:
                    data_flag, content = self.process_message(message)
                    # confirm message has been processed
                    container.get_connector('redis_stream_client')._client.xack(
                        stream_name, group_name, message_id
                    )
            if data_flag:
                contents = []
                while True:
                    print(f"{Fore.GREEN}{content}(Waiting for input. Your input can only be text or image path each time, you can press Enter once to input multiple times. Press Enter twice to finish the entire input.):{Style.RESET_ALL}")
                    user_input_lines = []
                    while True:
                        line = input(f"{Fore.GREEN}>>>{Style.RESET_ALL}")
                        if line == "":
                            break
                        user_input_lines.append(line)
                    logging.info(f"User input lines: {user_input_lines}")
                    
                
                    for user_input in user_input_lines:
                        if self.is_url(user_input) or self.is_file(user_input):
                            contents.append({
                                "type": "image_url",
                                "data": user_input
                            })
                        else:
                            contents.append({
                                "type": "text",
                                "data": user_input
                            })
                    if len(contents) > 0:
                        break
                result = {
                    "agent_id": workflow_instance_id,
                    "messages": [
                        {
                            "role": "user",
                            "content": contents
                        }
                    ],
                    "kwargs": {}    
                }
                container.get_connector('redis_stream_client')._client.xadd(f"{workflow_instance_id}_input", {"payload":json.dumps(result, ensure_ascii=False) })
            # Sleep for the specified interval before checking for new messages again
            # logging.info(f"Sleeping for {poll_interval} seconds, waiting for {stream_name} ...")
            #sleep(poll_interval)
            #line = input(f"{Fore.GREEN}>>>{Style.RESET_ALL}")
            #if line == "":
            #    break
            #user_input_lines.append(line)
        #return result
    
    

    def start_interactor(self):        
        absolute_path = Path(self._config_path).resolve()
        print(f"{absolute_path}")
        worker_config = build_from_file(self._config_path)
        print("worker_config:",worker_config)
        for config in worker_config:
            worker_cls = registry.get_worker(config['name'])
            self.workers[config['name']] = worker_cls(**config)       
        self.execute_workflow()
        
        