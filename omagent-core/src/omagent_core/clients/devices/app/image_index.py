import asyncio
import time
import json
from omagent_core.engine.http.models.workflow_status import running_status
from omagent_core.utils.registry import registry
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.container import container
from omagent_core.engine.orkes.orkes_workflow_client import workflow_client
from omagent_core.engine.configuration.configuration import Configuration
from omagent_core.utils.logger import logging



@registry.register_worker()
class ImageIndexListener(BaseWorker):
    def _run(self):
        stream_name = f"image_process"
        group_name = "omappagent"  # consumer group name
        consumer_name = f"image_agent"  # consumer name
        poll_interval: int = 1
        current_timestamp = int(time.time() * 1000)
        start_id = f"{current_timestamp}-0"

        result = {}
        # ensure consumer group exists
        try:
            container.get_connector("redis_stream_client")._client.xgroup_create(
                stream_name, group_name, id="0", mkstream=True
            )
        except Exception as e:
            logging.debug(f"Consumer group may already exist: {e}")

        logging.info(f"Listening to Redis stream: {stream_name} in group: {group_name}")
        flag = False
        while True:
            try:
                # logging.info(f"Checking workflow status: {self.workflow_instance_id}")
                workflow_status = workflow_client.get_workflow_status(self.workflow_instance_id)
                if workflow_status.status not in running_status:
                    logging.info(f"Workflow {self.workflow_instance_id} is not running, exiting...")
                    break

                # read new messages from redis stream
                messages = container.get_connector("redis_stream_client")._client.xrevrange(stream_name, max='+', min=start_id, count=1)
                # Convert byte data to string
                messages = [
                    (message_id, {k.decode('utf-8'): v.decode('utf-8') for k, v in message.items()}) for message_id, message in messages
                ]
                # logging.info(f"Messages: {messages}")

                for message_id, message in messages:
                    flag = self.process_message(message, result)
                    # confirm message has been processed
                    container.get_connector("redis_stream_client")._client.xack(
                        stream_name, group_name, message_id
                    )
                if flag:
                    break
                # Sleep for the specified interval before checking for new messages again
                # logging.info(f"Sleeping for {poll_interval} seconds, waiting for {stream_name} ...")
                time.sleep(poll_interval)
            except Exception as e:
                logging.error(f"Error while listening to stream: {e}")
                time.sleep(poll_interval)  # Wait before retrying
        return {"output": result}

    def process_message(self, message, result):
        logging.info(f"Received message: {message}")
        try:
            payload = message.get("payload")
            '''
            {
                "content": [
                    {
                    "type": "string",
                    "resource_id": "string",
                    "data": "string"
                    }
                ]
            }
            '''
            # check payload data
            if not payload:
                logging.error("Payload is empty")
                return False

            try:
                payload_data = json.loads(payload)
            except json.JSONDecodeError as e:
                logging.error(f"Payload is not a valid JSON: {e}")
                return False

            if "content" not in payload_data:
                logging.error("Payload does not contain 'content' key")
                return False

            if not isinstance(payload_data["content"], list):
                logging.error("'content' should be a list")
                return False

            for item in payload_data["content"]:
                if not isinstance(item, dict):
                    logging.error("Each item in 'content' should be a dictionary")
                    return False
                if "type" not in item or "resource_id" not in item or "data" not in item:
                    logging.error("Each item in 'content' should contain 'type', 'resource_id' and 'data' keys")
                    return False
            message_data = json.loads(payload)
            result.update(message_data)
        except Exception as e:
            logging.error(f"Error processing message: {e}")
            return False
        return True
