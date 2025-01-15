import logging

import requests
from omagent_core.engine.task_client import TaskClient


class ConductorLogHandler(logging.Handler):
    def __init__(self, task_client):
        super().__init__()
        self.task_client: TaskClient = task_client
        self.task_id = None

    def set_task_id(self, task_id):
        self.task_id = task_id

    def emit(self, record):
        if not self.task_id:
            return super().emit(record)
        log_entry = self.format(record)
        try:
            self.task_client.log(log_entry, self.task_id)
        except requests.exceptions.RequestException as e:
            print(f"Failed to send log to Conductor: {e}")
