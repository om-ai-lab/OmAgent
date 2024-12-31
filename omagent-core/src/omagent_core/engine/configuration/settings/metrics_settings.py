import logging
import os
from pathlib import Path

from omagent_core.engine.configuration.configuration import Configuration

logger = logging.getLogger(Configuration.get_logging_formatted_name(__name__))


def get_default_temporary_folder() -> str:
    return f"{str(Path.home())}/tmp/"


class MetricsSettings:
    def __init__(
        self,
        directory: str = None,
        file_name: str = "metrics.log",
        update_interval: float = 0.1,
    ):
        if directory is None:
            directory = get_default_temporary_folder()
        self.__set_dir(directory)
        self.file_name = file_name
        self.update_interval = update_interval

    def __set_dir(self, dir: str) -> None:
        if not os.path.isdir(dir):
            try:
                os.mkdir(dir)
            except Exception as e:
                logger.warning("Failed to create metrics temporary folder, reason: ", e)
        self.directory = dir
