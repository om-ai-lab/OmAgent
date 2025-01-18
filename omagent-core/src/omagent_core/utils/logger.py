import inspect
import logging as _logging
import logging.handlers as handlers
import os
from distutils.util import strtobool

from omagent_core.utils.container import container


class Logger(_logging.Logger):
    def __init__(self):
        pass

    def init_logger(
        self,
        name,
        log_name,
        level=None,
        roate="midnight",
        backup_count=30,
    ):
        """
        :param name: Name of the logger.
        :param log_name: Name of the log file.
        :param log_dir: The directory to save log files.
        :param level: Log level: The lowest level of log.
        :param Rotate: How to rotate log files.
        :param backup_count: How many log files to keep.
        """
        if level is None:
            level = (
                _logging.DEBUG if container.conductor_config.debug else _logging.INFO
            )
        super().__init__(name, level)

        formatter = _logging.Formatter(
            "%(levelname)s | %(asctime)s | %(pathname)s:%(lineno)d | %(funcName)s | %(message)s"
        )

        if not self.handlers:
            console_handler = _logging.StreamHandler()
            self.addHandler(console_handler)
            console_handler.setFormatter(formatter)

    def _log_with_caller_info(self, level, msg, *args, **kwargs):
        if self.isEnabledFor(level):
            frame = inspect.currentframe()
            outer_frames = inspect.getouterframes(frame)
            if len(outer_frames) > 3:
                calling_frame = outer_frames[3].frame
                self.findCaller = lambda *args: (
                    calling_frame.f_code.co_filename,
                    calling_frame.f_lineno,
                    calling_frame.f_code.co_name,
                    None,
                )
            self._log(level, msg, args, **kwargs)
            # Reset the findCaller to default after logging
            self.findCaller = _logging.Logger.findCaller

    def debug(self, msg, *args, **kwargs):
        self._log_with_caller_info(_logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._log_with_caller_info(_logging.INFO, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._log_with_caller_info(_logging.ERROR, msg, *args, **kwargs)


logging = Logger()
