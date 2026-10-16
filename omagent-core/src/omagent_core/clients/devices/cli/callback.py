import datetime
import os
import sys

from colorama import Fore, Style
from omagent_core.clients.base import CallbackBase
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry


@registry.register_component()
class DefaultCallback(CallbackBase):
    bot_id: str = ""
    incomplete_flag: bool = False

    def visualize_in_terminal(self, *args, **kwargs):
        pass

    def info(self, agent_id, progress, message):
        logging.info(
            f"\n{Fore.BLUE}info:{agent_id} {progress} {message}{Style.RESET_ALL}"
        )

    def show_image(self, agent_id, progress, image):
        """
        For CLI, just log that we would display an image.
        
        Args:
            agent_id (str): ID of the agent/workflow
            progress (str): Short description about the image
            image: Can be a URL string, base64 string, or PIL Image object
        """
        image_type = "URL" if isinstance(image, str) and image.startswith(('http://', 'https://')) else "base64/PIL"
        logging.info(
            f"\n{Fore.MAGENTA}image:{agent_id} {progress} [Image would be displayed in WebpageClient - {image_type}]{Style.RESET_ALL}"
        )

    def info_image(self, agent_id, progress, image):
        """
        For CLI, just log that we would display an image in the info panel.
        
        Args:
            agent_id (str): ID of the agent/workflow
            progress (str): Short description about the image
            image: Can be a URL string, base64 string, or PIL Image object
        """
        image_type = "URL" if isinstance(image, str) and image.startswith(('http://', 'https://')) else "base64/PIL"
        logging.info(
            f"\n{Fore.CYAN}info_image:{agent_id} {progress} [Image would be displayed in info panel - {image_type}]{Style.RESET_ALL}"
        )

    def send_incomplete(self, agent_id, msg, **kwargs):
        sys.stdout.write(f"{Fore.BLUE}{msg}{Style.RESET_ALL}")
        sys.stdout.flush()
        self.incomplete_flag = True

    def send_block(self, agent_id, msg, **kwargs):
        if kwargs.get("filter_special_symbols", False):
            msg = self.filter_special_symbols_in_msg(msg)
        if self.incomplete_flag:
            sys.stdout.write(f"{Fore.BLUE}{msg}{Style.RESET_ALL}")
            sys.stdout.flush()
            self.incomplete_flag = False
        else:
            logging.info(f"\n{Fore.BLUE}block:{msg}{Style.RESET_ALL}")

    def error(self, agent_id, error_code, error_info, **kwargs):
        logging.error(f"\n{Fore.RED}{error_info}{Style.RESET_ALL}")

    def send_answer(self, agent_id, msg, **kwargs):
        if kwargs.get("filter_special_symbols", False):
            msg = self.filter_special_symbols_in_msg(msg)
        if self.incomplete_flag:
            sys.stdout.write(f"{Fore.BLUE}{msg}{Style.RESET_ALL}")
            sys.stdout.flush()
            self.incomplete_flag = False
        else:
            logging.info(f"\n{Fore.BLUE}answer:{msg}{Style.RESET_ALL}")

    def finish(self, **kwargs):
        def generate_tree(path, indent=""):
            tree_str = ""
            items = sorted(
                [
                    item
                    for item in os.listdir(path)
                    if os.path.isdir(os.path.join(path, item))
                ]
            )
            for i, item in enumerate(items):
                tree_str += f"{indent}|-- {item}\n"
                new_path = os.path.join(path, item)
                if os.path.isdir(new_path):
                    if i == len(items) - 1:
                        tree_str += generate_tree(new_path, indent + "    ")
                    else:
                        tree_str += generate_tree(new_path, indent + "|   ")
            return tree_str

        execution_flow = generate_tree(self.folder_name)
        with open(f"{self.folder_name}/execution_flow.txt", "w") as file:
            file.write(execution_flow)
        logging.info(
            f"{Fore.BLUE}Finish running at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Execution flow as follow:\n{execution_flow}"
            f"{Style.RESET_ALL}"
        )

    def send_markdown_data(self, data):
        import requests

        data = {"message": data}
        requests.post(self.endpoint, json=data)
