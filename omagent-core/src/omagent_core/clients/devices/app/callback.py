import json
import base64
from io import BytesIO

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
        """
        Display information in the info panel.
        
        Args:
            agent_id (str): ID of the agent/workflow
            progress (str): Short description of the information
            message (str): The information message
        """
        # Check if message is a workflow JSON that should be visualized
        if progress == "Workflow" and isinstance(message, str):
            try:
                # Check if it looks like a workflow JSON with tasks
                data = json.loads(message)
                if isinstance(data, dict) and "tasks" in data and "name" in data:
                    try:
                        # Try to import and use the visualizer
                        from omagent_core.clients.devices.utils.workflow_visualizer import visualize_workflow_graph
                        workflow_img = visualize_workflow_graph(data)
                        if workflow_img:
                            # Also visualize the workflow as a graph
                            self.info_image(agent_id, progress="Workflow Graph", image=workflow_img)
                    except ImportError:
                        # Visualizer not available, just show the JSON
                        pass
                    except Exception as e:
                        # Log but don't crash if visualization fails
                        logging.error(f"Workflow visualization error: {str(e)}")
            except:
                # Not JSON or other issue, just proceed with normal info
                pass
                
        # Normal info message handling
        stream_name = f"{agent_id}_running"
        data = {"agent_id": agent_id, "progress": progress, "message": message}
        payload = {"payload": json.dumps(data, ensure_ascii=False)}
        self.redis_stream_client._client.xadd(stream_name, payload)

    def show_image(self, agent_id, progress, image):
        """
        Display an image in the main chat interface.
        
        Args:
            agent_id (str): ID of the agent/workflow
            progress (str): Short description about the image (not displayed)
            image: Can be a URL string, base64 string, or PIL Image object
        """
        # Handle different image input types
        image_path = None
        
        if isinstance(image, str):
            if image.startswith(('http://', 'https://', 'data:image')):
                # URL or data URI
                image_path = image
            else:
                # Assume it's a base64 string
                image_path = image if image.startswith("data:image") else f"data:image/png;base64,{image}"
        else:
            # Assume it's a PIL Image
            try:
                buffered = BytesIO()
                image.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                image_path = f"data:image/png;base64,{img_str}"
            except Exception as e:
                logging.error(f"Failed to process image: {e}")
                return
        
        # Only send to chatbot output stream for displaying in the main chat
        self.send_block(
            agent_id=agent_id,
            msg=image_path,
            msg_type=MessageType.IMAGE_URL.value
        )
        
    def info_image(self, agent_id, progress, image):
        """
        Display an image in the info panel (right side).
        
        Args:
            agent_id (str): ID of the agent/workflow
            progress (str): Short description about the image
            image: Can be a URL string, base64 string, or PIL Image object
        """
        # For info panel display
        stream_name = f"{agent_id}_running"
        
        # Handle different image input types
        image_data = {}
        
        if isinstance(image, str):
            if image.startswith(('http://', 'https://', 'data:image')):
                # URL or data URI
                image_data = {
                    "type": "image_url", 
                    "url": image
                }
            else:
                # Assume it's a base64 string
                base64_data = image if image.startswith("data:image") else f"data:image/png;base64,{image}"
                image_data = {
                    "type": "image_base64",
                    "data": base64_data
                }
        else:
            # Assume it's a PIL Image
            try:
                buffered = BytesIO()
                image.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                base64_data = f"data:image/png;base64,{img_str}"
                image_data = {
                    "type": "image_base64",
                    "data": base64_data
                }
            except Exception as e:
                logging.error(f"Failed to process image: {e}")
                return
        
        # Send to info panel only
        info_data = {
            "agent_id": agent_id, 
            "progress": progress, 
            "message": "", 
            "image": image_data
        }
        info_payload = {"payload": json.dumps(info_data, ensure_ascii=False)}
        self.redis_stream_client._client.xadd(stream_name, info_payload)

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
