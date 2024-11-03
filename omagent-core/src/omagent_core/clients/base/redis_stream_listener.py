import asyncio
import time
import json
from omagent_core.handlers.redis_stream_handler import RedisHandler
from omagent_core.utils.registry import registry
from omagent_core.engine.worker.base import BaseWorker

@registry.register_worker()
class RedisStreamListener(BaseWorker):
    def _run(self, workflow_instance_id: str):
        stream_name = f"{workflow_instance_id}_input"
        group_name = "omappagent"  # consumer group name
        consumer_name = f"{workflow_instance_id}_agent"  # consumer name
        poll_interval: int = 1

        redis_handler: RedisHandler = RedisHandler()
        result = {}
        # ensure consumer group exists
        try:
            redis_handler.redis_client.xgroup_create(stream_name, group_name, id='0', mkstream=True)
        except Exception as e:
            print(f"Consumer group may already exist: {e}")

        print(f"Listening to Redis stream: {stream_name} in group: {group_name}")
        flag = False
        while True:
            try:
                # read new messages from consumer group
                messages = redis_handler.redis_client.xreadgroup(group_name, consumer_name, {stream_name: '>'}, count=1)
                print(f"Messages: {messages}")
                
                for stream, message_list in messages:
                    for message_id, message in message_list:
                        flag = self.process_message(message, result)
                        # confirm message has been processed
                        redis_handler.redis_client.xack(stream_name, group_name, message_id)
                if flag:
                    break
                # Sleep for the specified interval before checking for new messages again
                print(f"Sleeping for {poll_interval} seconds, waiting for new messages...")
                time.sleep(poll_interval)
            except Exception as e:
                print(f"Error while listening to stream: {e}")
                time.sleep(poll_interval)  # Wait before retrying
        return {"output": result}

    def process_message(self, message, result):
        print(f"Received message: {message}")
        try:
            payload = message.get("payload")
            message_data = json.loads(payload)
            result.update(message_data)
        except Exception as e:
            print(f"Error processing message: {e}")
            return False
        return True
