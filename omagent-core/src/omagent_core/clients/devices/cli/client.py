from pathlib import Path

from omagent_core.services.connectors.redis import RedisConnector
from omagent_core.utils.container import container

container.register_connector(name="redis_stream_client", connector=RedisConnector)
import json
from time import sleep

import yaml
from colorama import Fore, Style
from omagent_core.clients.devices.app.input import AppInput
from omagent_core.clients.devices.cli.callback import DefaultCallback
from omagent_core.engine.automator.task_handler import TaskHandler
from omagent_core.engine.http.models.workflow_status import (running_status,
                                                             terminal_status)
from omagent_core.engine.orkes.orkes_workflow_client import workflow_client
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.utils.build import build_from_file
from omagent_core.utils.container import container
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry

registry.import_module()

# container.register_stm(stm='RedisSTM')
container.register_callback(callback=DefaultCallback)
container.register_input(input=AppInput)


class DefaultClient:
    def __init__(
        self,
        interactor: ConductorWorkflow = None,
        processor: ConductorWorkflow = None,
        config_path: str = "./config",
        workers: list = [],
        input_prompt: str = None,
    ) -> None:
        self._interactor = interactor
        self._processor = processor
        self._config_path = config_path
        self._workers = workers
        self._input_prompt = input_prompt
        self._task_to_domain = {}

    def start_interactor(self):
        workflow_instance_id = None
        try:
            absolute_path = Path(self._config_path).resolve()
            worker_config = build_from_file(self._config_path)
            self._task_handler_interactor = TaskHandler(
                worker_config=worker_config, workers=self._workers, task_to_domain=self._task_to_domain
            )
            self._task_handler_interactor.start_processes()
            workflow_instance_id = self._interactor.start_workflow_with_input(
                workflow_input={}, task_to_domain=self._task_to_domain
            )

            stream_name = f"{workflow_instance_id}_output"
            consumer_name = f"{workflow_instance_id}_agent"  # consumer name
            group_name = "omappagent"  # replace with your consumer group name
            poll_interval = 1

            if self._input_prompt:
                self.first_input(
                    workflow_instance_id=workflow_instance_id,
                    input_prompt=self._input_prompt,
                )

            try:
                container.get_connector("redis_stream_client")._client.xgroup_create(
                    stream_name, group_name, id="0", mkstream=True
                )
            except Exception as e:
                logging.debug(f"Consumer group may already exist: {e}")

            while True:
                try:
                    status = self._interactor.get_workflow(
                        workflow_id=workflow_instance_id
                    ).status
                    if status in terminal_status:
                        break
                    data_flag = False
                    content = None
                    # logging.info(f"Checking workflow status: {workflow_instance_id}")
                    workflow_status = workflow_client.get_workflow_status(
                        workflow_instance_id
                    )
                    if workflow_status.status not in running_status:
                        logging.info(
                            f"Workflow {workflow_instance_id} is not running, exiting..."
                        )
                        break

                    # read new messages from consumer group
                    messages = container.get_connector(
                        "redis_stream_client"
                    )._client.xreadgroup(
                        group_name, consumer_name, {stream_name: ">"}, count=1
                    )
                    # Convert byte data to string
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
                    # logging.info(f"Messages: {messages}")

                    for stream, message_list in messages:
                        for message_id, message in message_list:
                            data_flag, content = self.process_message(message)
                            # confirm message has been processed
                            container.get_connector("redis_stream_client")._client.xack(
                                stream_name, group_name, message_id
                            )
                    if data_flag:
                        contents = []
                        while True:
                            print(
                                f"{Fore.GREEN}{content}(Waiting for input. Your input can only be text or image path each time, you can press Enter once to input multiple times. Press Enter twice to finish the entire input.):{Style.RESET_ALL}"
                            )
                            user_input_lines = []
                            while True:
                                line = input(f"{Fore.GREEN}>>>{Style.RESET_ALL}")
                                if line == "":
                                    break
                                user_input_lines.append(line)
                            logging.info(f"User input lines: {user_input_lines}")

                            for user_input in user_input_lines:
                                if self.is_url(user_input) or self.is_file(user_input):
                                    contents.append(
                                        {"type": "image_url", "data": user_input}
                                    )
                                else:
                                    contents.append(
                                        {"type": "text", "data": user_input}
                                    )
                            if len(contents) > 0:
                                break
                        result = {
                            "agent_id": workflow_instance_id,
                            "messages": [{"role": "user", "content": contents}],
                            "kwargs": {},
                        }
                        container.get_connector("redis_stream_client")._client.xadd(
                            f"{workflow_instance_id}_input",
                            {"payload": json.dumps(result, ensure_ascii=False)},
                        )
                    # Sleep for the specified interval before checking for new messages again
                    # logging.info(f"Sleeping for {poll_interval} seconds, waiting for {stream_name} ...")
                    sleep(poll_interval)
                except Exception as e:
                    logging.error(f"Error while listening to stream: {e}")
                    sleep(poll_interval)  # Wait before retrying
            self.stop_interactor()
        except KeyboardInterrupt:
            logging.info("\nDetected Ctrl+C, stopping workflow...")
            if workflow_instance_id is not None:
                self._interactor._executor.terminate(workflow_id=workflow_instance_id)
            raise

    def stop_interactor(self):
        self._task_handler_interactor.stop_processes()

    def start_processor(self):
        workflow_instance_id = None
        try:
            worker_config = build_from_file(self._config_path)
            self._task_handler_processor = TaskHandler(
                worker_config=worker_config, workers=self._workers, task_to_domain=self._task_to_domain
            )
            self._task_handler_processor.start_processes()
            workflow_instance_id = self._processor.start_workflow_with_input(
                workflow_input={}, task_to_domain=self._task_to_domain
            )
            user_input = input(
                f"{Fore.GREEN}Please input a folder path of images:(WaitPress Enter to finish the entire input.):\n>>>{Style.RESET_ALL}"
            )

            image_items = []
            idx = 0
            for image_file in Path(user_input).iterdir():
                if image_file.is_file() and image_file.suffix in [
                    ".png",
                    ".jpg",
                    ".jpeg",
                ]:
                    image_items.append(
                        {
                            "type": "image_url",
                            "resource_id": str(idx),
                            "data": str(image_file),
                        }
                    )
                    idx += 1
            result = {"content": image_items}
            container.get_connector("redis_stream_client")._client.xadd(
                f"image_process", {"payload": json.dumps(result, ensure_ascii=False)}
            )
            while True:
                status = self._processor.get_workflow(
                    workflow_id=workflow_instance_id
                ).status
                if status in terminal_status:
                    break

                sleep(1)
            self.stop_processor()
        except KeyboardInterrupt:
            logging.info("\nDetected Ctrl+C, stopping workflow...")
            if workflow_instance_id is not None:
                self._processor._executor.terminate(workflow_id=workflow_instance_id)
            raise

    def stop_processor(self):
        self._task_handler_processor.stop_processes()

    def process_message(self, message):
        logging.info(f"Received message: {message}")
        try:
            payload = message.get("payload")
            # check payload data
            if not payload:
                logging.error("Payload is empty")
                return False, None

            try:
                payload_data = json.loads(payload)
            except json.JSONDecodeError as e:
                logging.error(f"Payload is not a valid JSON: {e}")
                return False, None

            if (
                "interaction_type" in payload_data
                and payload_data["interaction_type"] == 1
            ):
                content = payload_data["message"]["content"]
                return True, content

        except Exception as e:
            logging.error(f"Error processing message: {e}")
            return False, None
        return False, None

    def is_file(self, path: str) -> bool:
        """
        Determine if the given string is a file

        :param path: File path string
        :return: Returns True if it is a file, otherwise returns False
        """
        import os

        try:
            return os.path.isfile(path)
        except Exception as e:
            logging.error(f"Error checking if path is a file: {e}")
            return False

    def is_url(self, url: str) -> bool:
        """
        Determine if the given string is a URL
        """
        import re

        return bool(re.match(r"^https?://", url))

    def first_input(self, workflow_instance_id: str, input_prompt=""):
        contents = []
        while True:
            print(
                f"{Fore.GREEN}{input_prompt}(Waiting for input. Your input can only be text or image path each time, you can press Enter once to input multiple times. Press Enter twice to finish the entire input.):{Style.RESET_ALL}"
            )
            user_input_lines = []
            while True:
                line = input(f"{Fore.GREEN}>>>{Style.RESET_ALL}")
                if line == "":
                    break
                user_input_lines.append(line)
            logging.info(f"User input lines: {user_input_lines}")

            for user_input in user_input_lines:
                if self.is_url(user_input) or self.is_file(user_input):
                    contents.append({"type": "image_url", "data": user_input})
                else:
                    contents.append({"type": "text", "data": user_input})
            if len(contents) > 0:
                break
        result = {
            "agent_id": workflow_instance_id,
            "messages": [{"role": "user", "content": contents}],
            "kwargs": {},
        }
        container.get_connector("redis_stream_client")._client.xadd(
            f"{workflow_instance_id}_input",
            {"payload": json.dumps(result, ensure_ascii=False)},
        )
