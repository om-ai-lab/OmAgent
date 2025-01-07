import html
import json
from time import sleep

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
        self._incomplete_message = ""
        self._custom_css = """
            #OmAgent {
                height: 100vh !important;
                max-height: calc(100vh - 190px) !important;
                overflow-y: auto;
            }
            
            .running-message {
                margin: 0;
                padding: 2px 4px;
                white-space: pre-wrap;
                word-wrap: break-word;
                font-family: inherit;
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
        """

    def start_interactor(self):
        worker_config = build_from_file(self._config_path)
        self._task_handler_interactor = TaskHandler(
            worker_config=worker_config, workers=self._workers
        )
        self._task_handler_interactor.start_processes()
        try:
            with gr.Blocks(title="OmAgent", css=self._custom_css) as chat_interface:
                chatbot = gr.Chatbot(
                    elem_id="OmAgent",
                    bubble_full_width=False,
                    type="messages",
                    height="100%",
                )

                chat_input = gr.MultimodalTextbox(
                    interactive=True,
                    file_count="multiple",
                    placeholder="Enter message or upload file...",
                    show_label=False,
                )

                chat_msg = chat_input.submit(
                    self.add_message, [chatbot, chat_input], [chatbot, chat_input]
                )
                bot_msg = chat_msg.then(
                    self.bot, chatbot, chatbot, api_name="bot_response"
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
        worker_config = build_from_file(self._config_path)
        self._task_handler_processor = TaskHandler(
            worker_config=worker_config, workers=self._workers
        )
        self._task_handler_processor.start_processes()

        try:
            with gr.Blocks(title="OmAgent", css=self._custom_css) as chat_interface:
                chatbot = gr.Chatbot(
                    elem_id="OmAgent",
                    bubble_full_width=False,
                    type="messages",
                    height="100%",
                )

                chat_input = gr.MultimodalTextbox(
                    interactive=True,
                    file_count="multiple",
                    placeholder="Enter message or upload file...",
                    show_label=False,
                )

                chat_msg = chat_input.submit(
                    self.add_processor_message,
                    [chatbot, chat_input],
                    [chatbot, chat_input],
                )
                bot_msg = chat_msg.then(
                    self.processor_bot, chatbot, chatbot, api_name="bot_response"
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

    def add_message(self, history, message):
        if self._workflow_instance_id is None:
            self._workflow_instance_id = self._interactor.start_workflow_with_input(
                workflow_input={}
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
        return history, gr.MultimodalTextbox(value=None, interactive=False)

    def add_processor_message(self, history, message):
        if self._workflow_instance_id is None:
            self._workflow_instance_id = self._processor.start_workflow_with_input(
                workflow_input={}
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
        return history, gr.MultimodalTextbox(value=None, interactive=False)

    def bot(self, history: list):
        stream_name = f"{self._workflow_instance_id}_output"
        consumer_name = f"{self._workflow_instance_id}_agent"  # consumer name
        group_name = "omappagent"  # replace with your consumer group name
        running_stream_name = f"{self._workflow_instance_id}_running"
        self._check_redis_stream_exist(stream_name, group_name)
        self._check_redis_stream_exist(running_stream_name, group_name)
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
                    progress = html.escape(payload_data.get("progress", ""))
                    message = html.escape(payload_data.get("message", ""))
                    formatted_message = (
                        f'<pre class="running-message">{progress}: {message}</pre>'
                    )
                    history.append({"role": "assistant", "content": formatted_message})
                    yield history

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
                        history.append(
                            {
                                "role": "assistant",
                                "content": {"path": message_item["content"]},
                            }
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
                            if self._incomplete_message != "":
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
                                self._incomplete_message = ""
                            else:
                                history.append(
                                    {
                                        "role": "assistant",
                                        "content": message_item["content"],
                                    }
                                )

                    yield history

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

    def processor_bot(self, history: list):
        history.append({"role": "assistant", "content": f"processing..."})
        yield history
        while True:
            status = self._processor.get_workflow(
                workflow_id=self._workflow_instance_id
            ).status
            if status in terminal_status:
                history.append({"role": "assistant", "content": f"completed"})
                yield history
                self._workflow_instance_id = None
                break
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
