from colorama import Fore, Style
from pydantic import BaseModel, model_validator
import json

from omagent_core.utils.error import VQLError
from omagent_core.utils.logger import logging
from omagent_core.utils.container import container
from omagent_core.clients.base import BaseCallback
from .schemas import ContentStatus, InteractionType, MessageType


class AppCallback(BaseCallback):
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

    def send_to_group(self, stream_name, group_name, data):
        print(f"Stream: {stream_name}, Group: {group_name}, Data: {data}")
        container.get_connector("RedisStreamHandler").redis_client.xadd(
            stream_name, data
        )
        try:
            container.get_connector("RedisStreamHandler").redis_client.xgroup_create(
                stream_name, group_name, id="0"
            )
        except Exception as e:
            print(f"Consumer group may already exist: {e}")

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
        self.send_to_group(stream_name, group_name, data)

    def send_incomplete(self, agent_id, took, msg_type, msg):
        self.send_base_message(
            agent_id,
            0,
            "",
            took,
            msg_type,
            msg,
            ContentStatus.INCOMPLETE.value,
            InteractionType.DEFAULT.value,
            0,
            0,
        )

    def send_block(
        self,
        agent_id,
        took,
        msg_type,
        msg,
        interaction_type=InteractionType.DEFAULT.value,
    ):
        self.send_base_message(
            agent_id,
            0,
            "",
            took,
            msg_type,
            msg,
            ContentStatus.END_BLOCK.value,
            interaction_type,
            0,
            0,
        )

    def send_answer(self, agent_id, took, msg_type, msg):
        self.send_base_message(
            agent_id,
            0,
            "",
            took,
            msg_type,
            msg,
            ContentStatus.END_ANSWER.value,
            InteractionType.DEFAULT.value,
            0,
            0,
        )

    def info(self, agent_id, progress, message):
        stream_name = f"{agent_id}_running"
        data = {"agent_id": agent_id, "progress": progress, "message": message}
        payload = {"payload": json.dumps(data, ensure_ascii=False)}
        container.get_connector("RedisStreamHandler").send_to_stream(
            stream_name, payload
        )

    def error(self, agent_id, code, error_info):
        self.send_base_message(
            agent_id,
            code,
            error_info,
            0,
            MessageType.TEXT.value,
            "",
            "end_answer",
            0,
            0,
        )

    def finish(self, agent_id, took, type, msg):
        self.send_answer(agent_id, took, type, msg)
