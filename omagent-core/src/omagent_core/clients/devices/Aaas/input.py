import json
import time

from omagent_core.clients.devices.Aaas.schemas import (ConversationEvent, MessageType)
from omagent_core.clients.input_base import InputBase
from omagent_core.engine.http.models.workflow_status import running_status
from omagent_core.engine.orkes.orkes_workflow_client import (
    workflow_client)
from omagent_core.services.connectors.redis import RedisConnector
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry


@registry.register_component()
class AaasInput(InputBase):
    redis_stream_client: RedisConnector
    
    def read_input(self, workflow_instance_id: str, input_prompt=""):
        result = self._parse_workflow_instance_id(workflow_instance_id)
        workflow_instance_id = result.get('workflow_instance_id', '')
        agent_id = result.get('agent_id', '')
        conversation_id = result.get('conversation_id', '')
        chat_id = result.get('chat_id', '')
        
        stream_name = f"agent_os:conversation:input:{workflow_instance_id}"
        group_name = "OmAaasAgentConsumerGroup"  # consumer group name
        consumer_name = f"{workflow_instance_id}_agent"  # consumer name
        poll_interval: int = 1
        
        if input_prompt is not None:
            start_id = self.send_output_message(agent_id, conversation_id, chat_id, input_prompt)
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
                logging.info(f"Messages: {messages}")
                
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
            messages = []
            for dialong in payload.get('messages', []):
                content = []
                for item in dialong.get('contents', []):
                    content.append({
                        'type': item.get('contentType', 'unknown'),
                        'data': item.get('content')
                    })
                messages.append({
                    'role': dialong.get('role'),
                    'content': content
                })
            payload['messages'] = messages
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

    @staticmethod
    def _parse_workflow_instance_id(data: str):
        split_data = data.split('|')
        if not split_data:
            return {}
        result = {}
        keys = [
            'workflow_instance_id',
            'agent_id',
            'conversation_id',
            'chat_id',
        ]
        for index, value in enumerate(split_data):
            if index + 1 <= len(keys):
                result.setdefault(keys[index], value)
        return result
    
    def _create_output_data(
            self,
            event='',
            conversation_id='',
            chat_id='',
            agent_id='',
            status='',
            contentType='',
            content='',
            type='',
            is_finish=True
    ):
        data = {
            'content': json.dumps({
                'event': event,
                'data': {
                    'conversationId': conversation_id,
                    'chatId': chat_id,
                    'agentId': agent_id,
                    'createTime': None,
                    'endTime': None,
                    'status': status,
                    'contentType': contentType,
                    'content': content,
                    'type': type,
                    'isFinish': is_finish
                }
            }, ensure_ascii=False)
        }
        return data
    
    def send_base_message(
            self,
            event='',
            conversation_id='',
            chat_id='',
            agent_id='',
            status='',
            contentType='',
            content='',
            type='',
            is_finish=True
    ):
        stream_name = f"agent_os:conversation:output:{conversation_id}"
        group_name = "OmAaasAgentConsumerGroup"  # replace with your consumer group name
        message = self._create_output_data(
            event=event,
            conversation_id=conversation_id,
            chat_id=chat_id,
            agent_id=agent_id,
            status=status,
            contentType=contentType,
            content=content,
            type=type,
            is_finish=is_finish
        )
        message_id = self.send_to_group(stream_name, group_name, message)
        return message_id
    
    def send_output_message(
            self,
            agent_id,
            conversation_id,
            chat_id,
            msg,
    ):
        return self.send_base_message(
            event=ConversationEvent.MESSAGE_DELTA.value,
            conversation_id=conversation_id,
            chat_id=chat_id,
            agent_id=agent_id,
            status='completed',
            contentType=MessageType.TEXT.value,
            content=msg,
            type='ask_complete',
            is_finish=True
        )
    
    def send_to_group(self, stream_name, group_name, data):
        logging.info(f"Stream: {stream_name}, Group: {group_name}, Data: {data}")
        message_id = self.redis_stream_client._client.xadd(stream_name, data)
        try:
            self.redis_stream_client._client.xgroup_create(
                stream_name, group_name, id="0"
            )
        except Exception as e:
            logging.debug(f"Consumer group may already exist: {e}")
        
        return message_id
    