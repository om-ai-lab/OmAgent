import html
import json
from time import sleep
import re

import gradio as gr
from omagent_core.clients.devices.app.callback import AppCallback
from omagent_core.clients.devices.app.input import AppInput
from omagent_core.clients.devices.app.schemas import ContentStatus, MessageType
from omagent_core.engine.automator.task_handler import TaskHandler
from omagent_core.engine.http.models.workflow_status import terminal_status
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.services.connectors.redis import RedisConnector
from omagent_core.utils.build import build_from_file
from omagent_core.utils.container import container
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry

registry.import_module()

container.register_connector(name="redis_stream_client", connector=RedisConnector)
# container.register_stm(stm='RedisSTM')
container.register_callback(callback=AppCallback)
container.register_input(input=AppInput)


class WebpageClient:
    def __init__(
        self,
        interactor: ConductorWorkflow = None,
        processor: ConductorWorkflow = None,
        config_path: str = "./config",
        workers: list = [],
    ) -> None:
        self._interactor = interactor
        self._processor = processor
        self._config_path = config_path
        self._workers = workers
        self._workflow_instance_id = None
        self._worker_config = build_from_file(self._config_path)
        self._task_to_domain = {}
        self._incomplete_message = ""
        self._custom_css = """
            body {
                background-color: #16171b;
                font-family: 'Arial', sans-serif;
                color: #e0e0e0;
                margin: 0;
                padding: 0;
                height: 100vh;
                overflow: hidden;
            }
            
            .gradio-container {
                max-width: 100% !important;
                margin: 0 !important;
                padding: 0 !important;
                height: 100vh !important;
                overflow: hidden;
            }
            
            #header {
                margin: 0;
                padding: 15px;
                border-bottom: 1px solid #2d2e33;
            }
            
            #header h2 {
                margin: 0;
                color: #2196f3;
                font-weight: bold;
            }
            
            #main-content {
                display: flex !important;
                flex-direction: row !important;
                height: calc(100vh - 80px) !important;
                padding: 0 !important;
                margin: 0 !important;
                max-width: 100% !important;
            }
            
            #chat-column {
                flex: 1 !important; 
                position: relative;
                padding: 0;
                border-right: 1px solid #2d2e33;
                max-width: 50% !important;
                width: 50% !important;
            }
            
            #info-column {
                flex: 1 !important;
                padding: 0 !important;
                position: relative;
                background-color: #1e1f24;
                max-width: 50% !important;
                width: 50% !important;
            }
            
            #OmAgent {
                height: calc(100vh - 160px) !important;
                overflow-y: auto;
                background-color: #16171b !important;
                border-radius: 0 !important;
                box-shadow: none !important;
                margin: 0 !important;
                padding: 20px !important;
            }
            
            #info-panel {
                height: calc(100vh - 80px) !important;
                overflow-y: auto;
                background-color: #1e1f24;
                border-radius: 0;
                margin: 0;
                padding: 20px;
                font-family: 'Consolas', monospace;
                font-size: 14px;
                line-height: 1.5;
                color: #ddd;
            }
            
            /* Log styling for info panel */
            .log-container {
                display: flex;
                flex-direction: column;
                gap: 4px;
            }
            
            .log-entry {
                padding: 6px 10px;
                border-radius: 4px;
                background-color: #252830;
                border-left: 3px solid #2196f3;
                font-family: 'Consolas', monospace;
                word-break: break-word;
                animation: fadeIn 0.3s ease-in-out;
                white-space: pre-wrap;
            }
            
            /* JSON formatting styles */
            .json-container {
                font-family: 'Consolas', monospace;
                padding: 8px;
                border-radius: 4px;
                background-color: #252830;
                border-left: 3px solid #f1c40f; /* Yellow border for JSON */
                white-space: pre-wrap;
                overflow-x: auto;
            }
            
            .json-key {
                color: #f1c40f; /* Yellow */
            }
            
            .json-string {
                color: #2ecc71; /* Green */
            }
            
            .json-number {
                color: #9b59b6; /* Purple */
            }
            
            .json-boolean {
                color: #3498db; /* Blue */
            }
            
            .json-null {
                color: #e74c3c; /* Red */
            }
            
            /* Image styling in info panel */
            .image-container {
                margin: 10px 0;
                text-align: center;
            }
            
            .info-image {
                max-width: 100%;
                max-height: 500px;
                border-radius: 6px;
                border: 1px solid #2d2e33;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                margin-top: 10px;
            }
            
            .log-entry img {
                max-width: 100%;
                max-height: 500px;
                border: 1px solid #2d2e33;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                display: block;
                margin: 10px auto;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(4px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .progress {
                font-weight: bold;
                color: #2196f3;
                margin-right: 5px;
            }
            
            .message {
                margin-bottom: 10px !important;
                padding: 12px !important;
                border-radius: 8px !important;
                max-width: 85% !important;
            }
            
            .user-message {
                background-color: #2d5a8a !important;
                color: white !important;
            }
            
            .assistant-message {
                background-color: #2d2e33 !important;
                color: #e0e0e0 !important;
            }
            
            .running-message {
                margin: 0;
                padding: 2px 4px;
                white-space: pre-wrap;
                word-wrap: break-word;
                font-family: inherit;
            }

            .error-message {
                background-color: #f8d7da;
                color: #721c24;
                margin: 0;
                padding: 2px 4px;
                white-space: pre-wrap;
                word-wrap: break-word;
                font-family: inherit;
            }
            
            /* Input area styling */
            #input-area {
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                padding: 15px;
                background-color: #16171b;
                border-top: 1px solid #2d2e33;
            }
            
            .input-area {
                background-color: #2d2e33 !important;
                border: none !important;
                border-radius: 8px !important;
                color: #e0e0e0 !important;
            }
            
            /* Buttons */
            button {
                background-color: #2196f3 !important;
                color: white !important;
                border: none !important;
                border-radius: 6px !important;
                font-weight: 500 !important;
                transition: all 0.2s ease !important;
            }
            
            button:hover {
                background-color: #1976d2 !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
            }
            
            /* Remove the background and border of the message box */
            .message-wrap {
                background: none !important;
                border: none !important;
                padding: 0 !important;
                margin: 0 !important;
            }
            
            /* Remove the bubble style of the running message */
            .message:has(.running-message) {
                background: none !important;
                border: none !important;
                padding: 0 !important;
                box-shadow: none !important;
            }
            
            /* Fix Gradio's default containers */
            .contain {
                container-type: normal !important;
            }
            
            /* Override Gradio's column layout */
            .gr-col-lg-6 {
                width: auto !important;
                flex-grow: 1 !important;
            }
            
            /* Fix any Gradio padding/margins to maximize space */
            .gradio-container .prose {
                max-width: 100% !important;
                padding: 0 !important;
                margin: 0 !important;
            }
            
            .form {
                margin-bottom: 0 !important;
            }
            
            /* Style scrollbars */
            ::-webkit-scrollbar {
                width: 8px;
                height: 8px;
            }
            
            ::-webkit-scrollbar-track {
                background: #16171b;
            }
            
            ::-webkit-scrollbar-thumb {
                background: #2d2e33;
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: #3e3f44;
            }
        """

    def _is_json(self, text):
        """Check if a string appears to be valid JSON."""
        text = text.strip()
        return (text.startswith('{') and text.endswith('}')) or (text.startswith('[') and text.endswith(']'))
    
    def _format_json(self, json_str):
        """Format JSON with syntax highlighting."""
        try:
            # Parse and re-format with indentation
            parsed_json = json.loads(json_str)
            formatted_json = json.dumps(parsed_json, indent=2)
            
            # Add syntax highlighting with HTML
            # Replace quotes and then HTML escape to prevent injection
            formatted_json = html.escape(formatted_json)
            
            # Apply syntax highlighting with regex and HTML spans
            # Highlight keys
            formatted_json = re.sub(r'"([^"]+)"\s*:', r'<span class="json-key">"\1"</span>:', formatted_json)
            
            # Highlight string values
            formatted_json = re.sub(r':\s*"([^"]*)"', r': <span class="json-string">"\1"</span>', formatted_json)
            
            # Highlight numbers
            formatted_json = re.sub(r':\s*(-?\d+\.?\d*)', r': <span class="json-number">\1</span>', formatted_json)
            
            # Highlight booleans
            formatted_json = re.sub(r':\s*(true|false)', r': <span class="json-boolean">\1</span>', formatted_json)
            
            # Highlight null
            formatted_json = re.sub(r':\s*(null)', r': <span class="json-null">\1</span>', formatted_json)
            
            return f'<div class="json-container">{formatted_json}</div>'
            
        except json.JSONDecodeError:
            # If JSON parsing fails, return the original string wrapped in pre tags
            return f'<pre>{html.escape(json_str)}</pre>'

    def start_interactor(self):
        self._task_handler_interactor = TaskHandler(
            worker_config=self._worker_config, workers=self._workers, task_to_domain=self._task_to_domain
        )
        self._task_handler_interactor.start_processes()
        try:
            with gr.Blocks(title="OmAgent", css=self._custom_css) as chat_interface:
                # Remove tabs and just use a simple header
                with gr.Row(elem_id="header"):
                    gr.HTML("<h2>OmAgent</h2>")
                
                # Ensure columns are properly structured
                with gr.Row(elem_id="main-content"):
                    # Left column - Chat
                    with gr.Column(elem_id="chat-column"):
                        chatbot = gr.Chatbot(
                            elem_id="OmAgent",
                            bubble_full_width=False,
                            type="messages",
                            height="450px",
                        )

                        with gr.Row(elem_id="input-area"):
                            chat_input = gr.MultimodalTextbox(
                                interactive=True,
                                file_count="multiple",
                                placeholder="Enter message or upload file...",
                                show_label=False,
                                elem_classes=["input-area"],
                            )
                    
                    # Right column - Info Panel with fixed width
                    with gr.Column(elem_id="info-column"):
                        info_panel = gr.HTML(
                            elem_id="info-panel",
                            value="<div class='log-container'></div>",
                            label="Info"
                        )

                chat_msg = chat_input.submit(
                    self.add_message, [chatbot, chat_input, info_panel], [chatbot, chat_input, info_panel]
                )
                bot_msg = chat_msg.then(
                    self.bot, [chatbot, info_panel], [chatbot, info_panel], api_name="bot_response"
                )
                bot_msg.then(
                    lambda: gr.MultimodalTextbox(interactive=True), None, [chat_input]
                )
            chat_interface.launch()
        except KeyboardInterrupt:
            logging.info("\nDetected Ctrl+C, stopping workflow...")
            if self._workflow_instance_id is not None:
                self._interactor._executor.terminate(
                    workflow_id=self._workflow_instance_id
                )
            raise

    def stop_interactor(self):
        self._task_handler_interactor.stop_processes()

    def start_processor(self):
        self._task_handler_processor = TaskHandler(
            worker_config=self._worker_config, workers=self._workers, task_to_domain=self._task_to_domain
        )
        self._task_handler_processor.start_processes()

        try:
            with gr.Blocks(title="OmAgent", css=self._custom_css) as chat_interface:
                # Remove tabs and just use a simple header
                with gr.Row(elem_id="header"):
                    gr.HTML("<h2>OmAgent</h2>")
                
                # Ensure columns are properly structured
                with gr.Row(elem_id="main-content"):
                    # Left column - Chat
                    with gr.Column(elem_id="chat-column"):
                        chatbot = gr.Chatbot(
                            elem_id="OmAgent",
                            bubble_full_width=False,
                            type="messages",
                            height="450px",
                        )

                        with gr.Row(elem_id="input-area"):
                            chat_input = gr.MultimodalTextbox(
                                interactive=True,
                                file_count="multiple",
                                placeholder="Enter message or upload file...",
                                show_label=False,
                                elem_classes=["input-area"],
                            )
                    
                    # Right column - Info Panel with fixed width
                    with gr.Column(elem_id="info-column"):
                        info_panel = gr.HTML(
                            elem_id="info-panel",
                            value="<div class='log-container'></div>",
                            label="Info"
                        )

                chat_msg = chat_input.submit(
                    self.add_processor_message,
                    [chatbot, chat_input, info_panel],
                    [chatbot, chat_input, info_panel],
                )
                bot_msg = chat_msg.then(
                    self.processor_bot, [chatbot, info_panel], [chatbot, info_panel], api_name="bot_response"
                )
                bot_msg.then(
                    lambda: gr.MultimodalTextbox(interactive=True), None, [chat_input]
                )
            chat_interface.launch(server_port=7861)
        except KeyboardInterrupt:
            logging.info("\nDetected Ctrl+C, stopping workflow...")
            if self._workflow_instance_id is not None:
                self._processor._executor.terminate(
                    workflow_id=self._workflow_instance_id
                )
            raise

    def stop_processor(self):
        self._task_handler_processor.stop_processes()

    def add_message(self, history, message, info_panel):
        if self._workflow_instance_id is None:
            self._workflow_instance_id = self._interactor.start_workflow_with_input(
                workflow_input={}, task_to_domain=self._task_to_domain
            )
        contents = []
        for x in message["files"]:
            history.append({"role": "user", "content": {"path": x}})
            contents.append({"type": "image_url", "data": x})
        if message["text"] is not None:
            history.append({"role": "user", "content": message["text"]})
            contents.append({"type": "text", "data": message["text"]})
        result = {
            "agent_id": self._workflow_instance_id,
            "messages": [{"role": "user", "content": contents}],
            "kwargs": {},
        }
        container.get_connector("redis_stream_client")._client.xadd(
            f"{self._workflow_instance_id}_input",
            {"payload": json.dumps(result, ensure_ascii=False)},
        )
        return history, gr.MultimodalTextbox(value=None, interactive=False), info_panel

    def add_processor_message(self, history, message, info_panel):
        if self._workflow_instance_id is None:
            self._workflow_instance_id = self._processor.start_workflow_with_input(
                workflow_input={}, task_to_domain=self._task_to_domain
            )
        image_items = []
        for idx, x in enumerate(message["files"]):
            history.append({"role": "user", "content": {"path": x}})
            image_items.append(
                {"type": "image_url", "resource_id": str(idx), "data": str(x)}
            )
        result = {"content": image_items}
        container.get_connector("redis_stream_client")._client.xadd(
            f"image_process", {"payload": json.dumps(result, ensure_ascii=False)}
        )
        return history, gr.MultimodalTextbox(value=None, interactive=False), info_panel

    def bot(self, history: list, info_panel: str):
        stream_name = f"{self._workflow_instance_id}_output"
        consumer_name = f"{self._workflow_instance_id}_agent"  # consumer name
        group_name = "omappagent"  # replace with your consumer group name
        running_stream_name = f"{self._workflow_instance_id}_running"
        self._check_redis_stream_exist(stream_name, group_name)
        self._check_redis_stream_exist(running_stream_name, group_name)
        
        # Initialize logs container
        logs = []
        
        while True:
            # read running stream
            running_messages = self._get_redis_stream_message(
                group_name, consumer_name, running_stream_name
            )
            for stream, message_list in running_messages:
                for message_id, message in message_list:
                    payload_data = self._get_message_payload(message)
                    if payload_data is None:
                        continue
                    
                    # Check if this is an image message
                    if "image" in payload_data:
                        progress = html.escape(payload_data.get("progress", ""))
                        image_data = payload_data["image"]
                        
                        if image_data["type"] == "image_url":
                            image_html = f'<div class="log-entry"><span class="progress">{progress}</span>: <div><img src="{image_data["url"]}" style="max-width:100%; border-radius:4px; margin-top:8px;"></div></div>'
                            logs.append(image_html)
                        elif image_data["type"] == "image_base64":
                            image_html = f'<div class="log-entry"><span class="progress">{progress}</span>: <div><img src="{image_data["data"]}" style="max-width:100%; border-radius:4px; margin-top:8px;"></div></div>'
                            logs.append(image_html)
                    else:
                        # Format running message
                        progress = html.escape(payload_data.get("progress", ""))
                        message_text = payload_data.get("message", "")
                        
                        # Check if message contains JSON and format it accordingly
                        if self._is_json(message_text):
                            formatted_content = self._format_json(message_text)
                            logs.append(f"<div class='log-entry'><span class='progress'>{progress}</span>: {formatted_content}</div>")
                        else:
                            # Escape HTML in regular messages
                            message_text = html.escape(message_text)
                            logs.append(f"<div class='log-entry'><span class='progress'>{progress}</span>: {message_text}</div>")
                    
                    # Update the info panel instead of adding to chat
                    info_panel = f"""<div class='log-container'>{''.join(logs)}</div>"""
                    
                    yield history, info_panel

                    container.get_connector("redis_stream_client")._client.xack(
                        running_stream_name, group_name, message_id
                    )
                    
            # read output stream
            messages = self._get_redis_stream_message(
                group_name, consumer_name, stream_name
            )
            finish_flag = False

            for stream, message_list in messages:
                for message_id, message in message_list:
                    incomplete_flag = False
                    payload_data = self._get_message_payload(message)
                    if payload_data is None:
                        continue
                    if payload_data["content_status"] == ContentStatus.INCOMPLETE.value:
                        incomplete_flag = True
                    message_item = payload_data["message"]
                    if message_item["type"] == MessageType.IMAGE_URL.value:
                        # Handle both URL and base64 image data
                        image_content = message_item["content"]
                        if isinstance(image_content, dict) and "path" in image_content:
                            # Handle existing format
                            history.append(
                                {
                                    "role": "assistant",
                                    "content": {"path": image_content["path"]},
                                }
                            )
                        else:
                            # Handle direct URL or base64 string
                            history.append(
                                {
                                    "role": "assistant",
                                    "content": {"path": image_content},
                                }
                            )
                    else:
                        if incomplete_flag:
                            self._incomplete_message = (
                                self._incomplete_message + message_item["content"]

                            )
                        else:
                            if incomplete_flag:
                                self._incomplete_message = (
                                    self._incomplete_message + message_item["content"]
                                )
                                if history and history[-1]["role"] == "assistant":
                                    history[-1]["content"] = self._incomplete_message
                                else:
                                    history.append(
                                        {
                                            "role": "assistant",
                                            "content": self._incomplete_message,
                                        }
                                    )
                            else:
                                history.append(
                                    {
                                        "role": "assistant",
                                        "content": message_item["content"],
                                    }
                                )

                    yield history, info_panel


                    container.get_connector("redis_stream_client")._client.xack(
                        stream_name, group_name, message_id
                    )

                    # check finish flag
                    if (
                        "interaction_type" in payload_data
                        and payload_data["interaction_type"] == 1
                    ):
                        finish_flag = True
                    if (
                        "content_status" in payload_data
                        and payload_data["content_status"]
                        == ContentStatus.END_ANSWER.value
                    ):
                        self._workflow_instance_id = None
                        finish_flag = True

            if finish_flag:
                break
            sleep(0.01)

    def processor_bot(self, history: list, info_panel: str):
        history.append({"role": "assistant", "content": f"processing..."})
        logs = []
        
        while True:
            status = self._processor.get_workflow(
                workflow_id=self._workflow_instance_id
            ).status
            
            # Add processing status to logs
            logs.append(f"<div class='log-entry'>Status: {status}</div>")
            info_panel = f"""<div class='log-container'>{''.join(logs)}</div>"""
            
            if status in terminal_status:
                history.append({"role": "assistant", "content": f"completed"})
                yield history, info_panel
                self._workflow_instance_id = None
                break
            
            yield history, info_panel
            sleep(0.01)

    def _get_redis_stream_message(
        self, group_name: str, consumer_name: str, stream_name: str
    ):
        messages = container.get_connector("redis_stream_client")._client.xreadgroup(
            group_name, consumer_name, {stream_name: ">"}, count=1
        )
        messages = [
            (
                stream,
                [
                    (
                        message_id,
                        {
                            k.decode("utf-8"): v.decode("utf-8")
                            for k, v in message.items()
                        },
                    )
                    for message_id, message in message_list
                ],
            )
            for stream, message_list in messages
        ]
        return messages

    def _check_redis_stream_exist(self, stream_name: str, group_name: str):
        try:
            container.get_connector("redis_stream_client")._client.xgroup_create(
                stream_name, group_name, id="0", mkstream=True
            )
        except Exception as e:
            logging.debug(f"Consumer group may already exist: {e}")

    def _get_message_payload(self, message: dict):
        logging.info(f"Received running message: {message}")
        payload = message.get("payload")
        # check payload data
        if not payload:
            logging.error("Payload is empty")
            return None
        try:
            payload_data = json.loads(payload)
        except json.JSONDecodeError as e:
            logging.error(f"Payload is not a valid JSON: {e}")
            return None
        return payload_data
