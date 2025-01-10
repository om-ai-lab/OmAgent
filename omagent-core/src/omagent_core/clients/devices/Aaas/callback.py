import json

from omagent_core.clients.base import CallbackBase
from omagent_core.services.connectors.redis import RedisConnector
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
from .schemas import ConversationEvent, InteractionType, MessageType


@registry.register_component()
class AaasCallback(CallbackBase):
    redis_stream_client: RedisConnector
    
    bot_id: str = ""
    
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
        self.send_to_group(stream_name, group_name, message)

    def send_to_group(self, stream_name, group_name, data):
        logging.info(f"Stream: {stream_name}, Group: {group_name}, Data: {data}")
        self.redis_stream_client._client.xadd(stream_name, data)
        try:
            self.redis_stream_client._client.xgroup_create(
                stream_name, group_name, id="0"
            )
        except Exception as e:
            logging.debug(f"Consumer group may already exist: {e}")
    
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
        
    def send_incomplete(
            self,
            agent_id,
            msg,
            took=0,
            msg_type=MessageType.TEXT.value,
            prompt_tokens=0,
            output_tokens=0,
            filter_special_symbols=True,
    ):
        result = self._parse_workflow_instance_id(agent_id)
        agent_id = result.get('agent_id', '')
        conversation_id = result.get('conversation_id', '')
        chat_id = result.get('chat_id', '')

        self.send_base_message(
            event=ConversationEvent.MESSAGE_DELTA.value,
            conversation_id=conversation_id,
            chat_id=chat_id,
            agent_id=agent_id,
            status='delta',
            contentType=msg_type,
            content=msg,
            type='answer',
            is_finish=False
        )
    
    def send_block(
            self,
            agent_id,
            msg,
            took=0,
            msg_type=MessageType.TEXT.value,
            interaction_type=InteractionType.DEFAULT.value,
            prompt_tokens=0,
            output_tokens=0,
            filter_special_symbols=True,
    ):
        result = self._parse_workflow_instance_id(agent_id)
        agent_id = result.get('agent_id', '')
        conversation_id = result.get('conversation_id', '')
        chat_id = result.get('chat_id', '')

        if interaction_type == InteractionType.DEFAULT.INPUT:
            self.send_base_message(
                event=ConversationEvent.MESSAGE_DELTA.value,
                conversation_id=conversation_id,
                chat_id=chat_id,
                agent_id=agent_id,
                status='completed',
                contentType=msg_type,
                content=msg,
                type='ask_complete',
                is_finish=True
            )
            return
        self.send_base_message(
            event=ConversationEvent.MESSAGE_DELTA.value,
            conversation_id=conversation_id,
            chat_id=chat_id,
            agent_id=agent_id,
            status='completed',
            contentType=msg_type,
            content=msg,
            type='answer',
            is_finish=True
        )
    
    def send_answer(
            self,
            agent_id,
            msg,
            took=0,
            msg_type=MessageType.TEXT.value,
            prompt_tokens=0,
            output_tokens=0,
            filter_special_symbols=True,
    ):
        result = self._parse_workflow_instance_id(agent_id)
        agent_id = result.get('agent_id', '')
        conversation_id = result.get('conversation_id', '')
        chat_id = result.get('chat_id', '')

        self.send_base_message(
            event=ConversationEvent.MESSAGE_COMPLETED.value,
            conversation_id=conversation_id,
            chat_id=chat_id,
            agent_id=agent_id,
            status='completed',
            contentType=msg_type,
            content=msg,
            type='answer',
            is_finish=True
        )
    
    def info(
            self,
            agent_id,
            msg,
            msg_type=MessageType.TEXT.value,
    ):
        result = self._parse_workflow_instance_id(agent_id)
        agent_id = result.get('agent_id', '')
        conversation_id = result.get('conversation_id', '')
        chat_id = result.get('chat_id', '')

        self.send_base_message(
            event=ConversationEvent.MESSAGE_DELTA.value,
            conversation_id=conversation_id,
            chat_id=chat_id,
            agent_id=agent_id,
            status='completed',
            contentType=msg_type,
            content=msg,
            type='runner_output',
            is_finish=True
        )
    
    def error(
            self,
            agent_id,
            msg,
            msg_type=MessageType.TEXT.value,
    ):
        result = self._parse_workflow_instance_id(agent_id)
        agent_id = result.get('agent_id', '')
        conversation_id = result.get('conversation_id', '')
        chat_id = result.get('chat_id', '')

        self.send_base_message(
            event=ConversationEvent.MESSAGE_ERROR.value,
            conversation_id=conversation_id,
            chat_id=chat_id,
            agent_id=agent_id,
            status='completed',
            contentType=msg_type,
            content=msg,
            type='runner_output',
            is_finish=True
        )
    
    def finish(self, agent_id, took, type, msg, prompt_tokens=0, output_tokens=0):
        self.send_answer(
            agent_id,
            msg=msg
        )
