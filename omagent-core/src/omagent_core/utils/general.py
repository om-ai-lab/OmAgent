import base64
import os
import platform
from collections import OrderedDict
from io import BytesIO
from pathlib import Path
from typing import Sequence

import requests
from PIL import Image
import yaml
from pathlib import Path
from mcp.client.stdio import StdioServerParameters
from omagent_core.services.handlers.mcp_client import MCPClient


class LRUCache:
    # initializing capacity
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity

    def has(self, key) -> bool:
        return key in self.cache

    # we return the value of the key
    # that is queried in O(1) and return -1 if we
    # don't find the key in out dict / cache.
    # And also move the key to the end
    # to show that it was recently used.
    def get(self, key, default=None):
        if key not in self.cache:
            return default
        else:
            self.cache.move_to_end(key)
            return self.cache[key]

    # first, we add / update the key by conventional methods.
    # And also move the key to the end to show that it was recently used.
    # But here we will also check whether the length of our
    # ordered dictionary has exceeded our capacity,
    # If so we remove the first key (least recently used)
    def put(self, key, value) -> None:
        self.cache[key] = value
        self.cache.move_to_end(key)
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

    def pop(self, key, value):
        self.cache.pop(key, None)


def handle_response(res, json, url):
    if res.status_code < 299:
        return res.json()
    elif res.status_code == 404:
        logging.error("Request URL: {} | Error[404]: 请求错误: 错误的地址".format(url))
        raise VQLError(516)
    elif res.status_code == 422:
        logging.error(
            "Request URL: {} | Request body: {} | Error[422]: 请求错误: 错误的请求格式".format(
                url, json
            )
        )
        raise VQLError(517)
    else:
        info = res.json()
        logging.error(
            "Request URL: {} | Request body: {} | Error: {}".format(url, json, info)
        )
        raise VQLError(511, detail=info)


def chunks(l: Sequence, win_len: int, stride_len: int):
    s_id = 0
    e_id = min(len(l), win_len)

    while True:
        yield l[s_id:e_id]

        if e_id == len(l):
            break

        s_id = s_id + stride_len
        e_id = min(s_id + win_len, len(l))


def encode_image(input):
    def _encode(img):
        output_buffer = BytesIO()
        img.save(output_buffer, format="JPEG")
        byte_data = output_buffer.getvalue()
        base64_str = base64.b64encode(byte_data)
        base64_str = str(base64_str, encoding="utf-8")
        return base64_str

    input = input.convert("RGB")
    if isinstance(input, list):
        res = []
        for img in input:
            res.append(_encode(img))
        return res
    else:
        return _encode(input)


def get_platform() -> str:
    """Get platform."""
    system = platform.system()
    if system == "Darwin":
        return "MacOS"
    return system


def read_image(input_source) -> Image.Image:
    """
    Read an image from a local path, URL, PIL Image object, or Path object.

    Args:
        input_source (str or PIL.Image.Image or Path): The source of the image.
            Can be a local file path, a URL, a PIL Image object, or a Path object.

    Returns:
        PIL.Image.Image: The image as a PIL Image object.

    Raises:
        ValueError: If the input source is invalid or the image cannot be read.
    """
    if isinstance(input_source, Image.Image):
        return input_source

    if isinstance(input_source, (str, Path)):
        if isinstance(input_source, str) and input_source.startswith(
            ("http://", "https://")
        ):
            # URL
            try:
                response = requests.get(input_source)
                response.raise_for_status()
                return Image.open(BytesIO(response.content))
            except requests.RequestException as e:
                raise ValueError(f"Failed to fetch image from URL: {e}")
        elif os.path.isfile(str(input_source)):
            # Local file path or Path object
            try:
                return Image.open(input_source)
            except IOError as e:
                raise ValueError(f"Failed to open local image file: {e}")
        else:
            raise ValueError(
                "Invalid input source. Must be a valid URL or local file path."
            )

    raise ValueError(
        "Invalid input type. Must be a string (URL or file path), Path object, or PIL Image object."
    )


def create_mcp_client_from_config(config_path: str) -> MCPClient:
    """
    Reads command, args, and env settings from a YAML config file,
    then returns an MCPClient instance based on those settings.
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")

    with open(config_file, "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    # Grab the relevant part of your config
    mcp_config = config.get("mcp", {}).get("server_params", {})
    command = mcp_config.get("command", "docker")
    args = mcp_config.get("args", [])
    env = mcp_config.get("env", {})

    # Create StdioServerParameters using loaded config
    server_params = StdioServerParameters(
        command=command,
        args=args,
        env=env
    )

    return MCPClient(server_params) 