import json
import time

from omagent_core.clients.devices.app.schemas import (CodeEnum, ContentStatus,
                                                      InteractionType,
                                                      MessageType)
from omagent_core.clients.input_base import InputBase
from omagent_core.engine.configuration.configuration import Configuration
from omagent_core.engine.http.models.workflow_status import running_status
from omagent_core.engine.orkes.orkes_workflow_client import (
    OrkesWorkflowClient, workflow_client)
from omagent_core.services.connectors.redis import RedisConnector
from omagent_core.utils import registry
from omagent_core.utils.container import container
from omagent_core.utils.general import read_image
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
import os

@registry.register_component()
class AppInput(InputBase):
    redis_stream_client: RedisConnector

    def read_input(self, workflow_instance_id: str, input_prompt=""):
        stream_name = f"{workflow_instance_id}_input"
        group_name = "omappagent"  # consumer group name
        consumer_name = f"{workflow_instance_id}_agent"  # consumer name
        poll_interval: int = 1

        if input_prompt is not None:
            start_id = self._send_input_message(workflow_instance_id, input_prompt)
        else:
            current_timestamp = int(time.time() * 1000)
            start_id = f"{current_timestamp}-0"

        result = {}
        # ensure consumer group exists
        try:
            self.redis_stream_client._client.xgroup_create(
                stream_name, group_name, id="0", mkstream=True
            )
        except Exception as e:
            logging.debug(f"Consumer group may already exist: {e}")

        if not os.getenv("OMAGENT_MODE") == "lite":
            logging.info(
                f"Listening to Redis stream: {stream_name} in group: {group_name} start_id: {start_id}"
            )
        
        data_flag = False
        while True:
            try:
                # logging.info(f"Checking workflow status: {workflow_instance_id}")
                workflow_status = workflow_client.get_workflow_status(
                    workflow_instance_id
                )
                if workflow_status.status not in running_status:
                    logging.info(
                        f"Workflow {workflow_instance_id} is not running, exiting..."
                    )
                    break

                # read new messages from redis stream
                messages = self.redis_stream_client._client.xrevrange(
                    stream_name, max="+", min=start_id, count=1
                )
                # Convert byte data to string
                messages = [
                    (
                        message_id,
                        {
                            k.decode("utf-8"): v.decode("utf-8")
                            for k, v in message.items()
                        },
                    )
                    for message_id, message in messages
                ]
                # logging.info(f"Messages: {messages}")

                for message_id, message in messages:
                    data_flag = self.process_message(message, result)
                if data_flag:
                    break
                # Sleep for the specified interval before checking for new messages again
                # logging.info(f"Sleeping for {poll_interval} seconds, waiting for {stream_name} ...")
                time.sleep(poll_interval)
            except Exception as e:
                logging.error(f"Error while listening to stream: {e}")
                time.sleep(poll_interval)  # Wait before retrying
        return result

    def process_message(self, message, result):
        logging.info(f"Received message: {message}")
        try:
            payload = message.get("payload")
            """
            {
                "agent_id": "string",
                "messages": [
                    {
                        "role": "string",
                        "content": [
                            {
                                "type": "string",
                                "data": "string"
                            }
                        ]
                    }
                ],
                "kwargs": {}
            }
            """
            # check payload data
            if not payload:
                logging.error("Payload is empty")
                return False

            try:
                payload_data = json.loads(payload)
            except json.JSONDecodeError as e:
                logging.error(f"Payload is not a valid JSON: {e}")
                return False

            if "agent_id" not in payload_data:
                logging.error("Payload does not contain 'agent_id' key")
                return False

            if "messages" not in payload_data:
                logging.error("Payload does not contain 'messages' key")
                return False

            if not isinstance(payload_data["messages"], list):
                logging.error("'messages' should be a list")
                return False

            for message in payload_data["messages"]:
                if not isinstance(message, dict):
                    logging.error("Each item in 'messages' should be a dictionary")
                    return False
                if "role" not in message or "content" not in message:
                    logging.error(
                        "Each item in 'messages' should contain 'role' and 'content' keys"
                    )
                    return False
                if not isinstance(message["content"], list):
                    logging.error("'content' should be a list")
                    return False
                for content in message["content"]:
                    if not isinstance(content, dict):
                        logging.error("Each item in 'content' should be a dictionary")
                        return False
                    if "type" not in content or "data" not in content:
                        logging.error(
                            "Each item in 'content' should contain 'type' and 'data' keys"
                        )
                        return False

            message_data = json.loads(payload)
            result.update(message_data)
        except Exception as e:
            logging.error(f"Error processing message: {e}")
            return False
        return True

    def _send_input_message(self, agent_id, msg):
        message_id = self._send_base_message(
            agent_id,
            CodeEnum.SUCCESS.value,
            "",
            0,
            MessageType.TEXT.value,
            msg,
            ContentStatus.END_BLOCK.value,
            InteractionType.INPUT.value,
            0,
            0,
        )
        return message_id

    def _create_message_data(
        self,
        agent_id,
        code,
        error_info,
        took,
        msg_type,
        msg,
        content_status,
        interaction_type,
        prompt_tokens,
        output_tokens,
    ):
        message = {"role": "assistant", "type": msg_type, "content": msg}
        usage = {"prompt_tokens": prompt_tokens, "output_tokens": output_tokens}
        data = {
            "agent_id": agent_id,
            "code": code,
            "error_info": error_info,
            "took": took,
            "content_status": content_status,
            "interaction_type": int(interaction_type),
            "message": message,
            "usage": usage,
        }
        return {"payload": json.dumps(data, ensure_ascii=False)}

    def _send_to_group(self, stream_name, group_name, data):
        logging.info(f"Stream: {stream_name}, Group: {group_name}, Data: {data}")
        message_id = self.redis_stream_client._client.xadd(stream_name, data)
        try:
            self.redis_stream_client._client.xgroup_create(
                stream_name, group_name, id="0"
            )
        except Exception as e:
            logging.debug(f"Consumer group may already exist: {e}")

        return message_id

    def _send_base_message(
        self,
        agent_id,
        code,
        error_info,
        took,
        msg_type,
        msg,
        content_status,
        interaction_type,
        prompt_tokens,
        output_tokens,
    ):
        stream_name = f"{agent_id}_output"
        group_name = "omappagent"  # replace with your consumer group name
        data = self._create_message_data(
            agent_id,
            code,
            error_info,
            took,
            msg_type,
            msg,
            content_status,
            interaction_type,
            prompt_tokens,
            output_tokens,
        )
        message_id = self._send_to_group(stream_name, group_name, data)
        return message_id
