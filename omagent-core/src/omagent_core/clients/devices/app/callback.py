import json

from omagent_core.clients.base import CallbackBase
from omagent_core.services.connectors.redis import RedisConnector
from omagent_core.utils.container import container
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry

from .schemas import CodeEnum, ContentStatus, InteractionType, MessageType


@registry.register_component()
class AppCallback(CallbackBase):
    redis_stream_client: RedisConnector

    bot_id: str = ""

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
        filter_special_symbols=True,
    ):
        if msg_type == MessageType.TEXT.value and filter_special_symbols:
            msg = self.filter_special_symbols_in_msg(msg)
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

    def send_to_group(self, stream_name, group_name, data):
        logging.info(f"Stream: {stream_name}, Group: {group_name}, Data: {data}")
        self.redis_stream_client._client.xadd(stream_name, data)
        try:
            self.redis_stream_client._client.xgroup_create(
                stream_name, group_name, id="0"
            )
        except Exception as e:
            logging.debug(f"Consumer group may already exist: {e}")

    def send_base_message(
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
        filter_special_symbols=True,
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
            filter_special_symbols,
        )
        self.send_to_group(stream_name, group_name, data)

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
        self.send_base_message(
            agent_id,
            CodeEnum.SUCCESS.value,
            "",
            took,
            msg_type,
            msg,
            ContentStatus.INCOMPLETE.value,
            InteractionType.DEFAULT.value,
            prompt_tokens,
            output_tokens,
            filter_special_symbols,
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
        self.send_base_message(
            agent_id,
            CodeEnum.SUCCESS.value,
            "",
            took,
            msg_type,
            msg,
            ContentStatus.END_BLOCK.value,
            interaction_type,
            prompt_tokens,
            output_tokens,
            filter_special_symbols,
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
        self.send_base_message(
            agent_id,
            CodeEnum.SUCCESS.value,
            "",
            took,
            msg_type,
            msg,
            ContentStatus.END_ANSWER.value,
            InteractionType.DEFAULT.value,
            prompt_tokens,
            output_tokens,
            filter_special_symbols,
        )

    def info(self, agent_id, progress, message):
        stream_name = f"{agent_id}_running"
        data = {"agent_id": agent_id, "progress": progress, "message": message}
        payload = {"payload": json.dumps(data, ensure_ascii=False)}
        self.redis_stream_client._client.xadd(stream_name, payload)

    def error(self, agent_id, error_code, error_info, prompt_tokens=0, output_tokens=0):
        self.send_base_message(
            agent_id,
            error_code,
            error_info,
            0,
            MessageType.TEXT.value,
            "",
            ContentStatus.END_ANSWER.value,
            InteractionType.DEFAULT.value,
            prompt_tokens,
            output_tokens,
        )

    def finish(self, agent_id, took, type, msg, prompt_tokens=0, output_tokens=0):
        self.send_answer(agent_id, took, type, msg, prompt_tokens, output_tokens)
