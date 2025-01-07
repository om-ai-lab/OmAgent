import requests
import json
from omagent_core.engine.http.models.task import Task
import logging

class AaasTaskApi(object):

    def __init__(self, configuration=None):
        self.configuration = configuration
    
    def batch_poll_from_aaas(self, tasktype, **kwargs):
        """Batch retrieve tasks from AaaS

        Args:
            tasktype (str): Required. The type of task to poll
            workerid (str): Optional. Worker node ID
            domain (str): Optional. Domain name
            count (int): Optional. Batch size
            
        Returns:
            list[Task]: List of Task objects
            If async_req=True, returns the request thread
        """
        kwargs['_return_http_data_only'] = True
        if kwargs.get('async_req'):
            return self.batch_poll_from_aaas_with_http_info(tasktype, **kwargs)
        else:
            (data) = self.batch_poll_from_aaas_with_http_info(tasktype, **kwargs)
            return data

    def batch_poll_from_aaas_with_http_info(self, tasktype, **kwargs):
        """Implementation of batch task retrieval from AaaS

        Args:
            tasktype (str): Required. The type of task to poll
            workerid (str): Optional. Worker node ID
            domain (str): Optional. Domain name
            count (int): Optional. Batch size
            
        Returns:
            list[Task]: List of Task objects
            If async_req=True, returns the request thread
        """
        url = self.configuration.host + "/v1/batchPoll"
        token = self.configuration.token
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        data = {
            "batchSize": kwargs.get('count', 1),
            "domain": kwargs.get('domain', None),
            "isProd": kwargs.get('is_prod', False),
            "taskDefName": tasktype,
            "workerId": kwargs.get('workerid', 'default_worker')
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            data_json = response.json()
            
            # Convert data structure to list of Task objects
            tasks = []
            if data_json.get('code') == 200 and data_json.get('data'):
                for task_data in data_json['data']:
                    # Create Task instance
                    task = Task()
                    
                    # Set basic properties
                    task.input_data = json.loads(task_data['payload']) if task_data.get('payload') else {}
                    task.reference_task_name = tasktype
                    task.status = 'IN_PROGRESS'
                    
                    # Parse bizMeta
                    if task_data.get('bizMeta'):
                        biz_meta = json.loads(task_data['bizMeta'])
                        task.workflow_instance_id = biz_meta.get('workflowInstanceId')
                        task.task_id = biz_meta.get('taskId')
                        task.biz_meta = task_data['bizMeta']
                    
                    # Add callback URL
                    if task_data.get('callbackUrl'):
                        task.callback_url = task_data['callbackUrl']
                        
                    tasks.append(task)
                    
            return tasks
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch tasks from AaaS: {str(e)}")
            raise

    def update_task_to_aaas(self, body, **kwargs):
        """Update task status to AaaS

        Example:
            >>> thread = api.update_task(body, async_req=True)
            >>> result = thread.get()

        Args:
            body (TaskResult): Required. The task result to update
            async_req (bool): Optional. If True, makes an asynchronous HTTP request
            
        Returns:
            str: Success indicator
            If async_req=True, returns the request thread
        """
        kwargs["_return_http_data_only"] = True
        if kwargs.get("async_req"):
            return self.update_task_to_aaas_with_http_info(body, **kwargs)
        else:
            (data) = self.update_task_to_aaas_with_http_info(body, **kwargs)
            return data


    def update_task_to_aaas_with_http_info(self, body, **kwargs):
        """Implementation of task status update to AaaS

        Args:
            body (TaskResult): Required. The task result to update
            
        Returns:
            bool: True if update successful, False otherwise
            If async_req=True, returns the request thread
        """
        url = self.configuration.host + "/v1/updateTaskStatus"
        token = self.configuration.token
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        data = {
            "bizMeta": body.biz_meta,
            "callbackUrl": body.callback_url,
            "logs": [{"createdTime":log.created_time, "log":log.log} for log in body.logs] if body.logs else [],
            "outputData": body.output_data,
            "reasonForIncompletion":body.reason_for_incompletion,
            "status": body.status,
            "taskId": body.task_id,
            "workId": body.worker_id
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            logging.debug(response.text)
            if response.status_code == 200:
                return True
            else:
                return False
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to update task to AaaS: {str(e)}")
            raise
