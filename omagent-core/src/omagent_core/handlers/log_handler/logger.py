import inspect
import logging as _logging
import logging.handlers as handlers
import os
from distutils.util import strtobool


class Logger(_logging.Logger):
    def __init__(self):
        pass

    def init_logger(
        self,
        name,
        log_name,
        log_dir="./logs",
        level=_logging.NOTSET,
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
        super().__init__(name, level)

        formatter = _logging.Formatter(
            "%(levelname)s | %(asctime)s | %(pathname)s:%(lineno)d | %(funcName)s | %(message)s"
        )

        if not self.handlers:
            console_handler = _logging.StreamHandler()
            self.addHandler(console_handler)
            console_handler.setFormatter(formatter)
            if not strtobool(os.environ.get("IS_DEBUG", "false")):
                logger_dir_path = os.path.join(log_dir, log_name)
                logger_file_path = os.path.join(logger_dir_path, f"{log_name}.log")
                os.makedirs(logger_dir_path, exist_ok=True)

                file_handler = handlers.TimedRotatingFileHandler(
                    logger_file_path,
                    when=roate,
                    backupCount=backup_count,
                    encoding="utf-8",
                )
                file_handler.suffix = "-%Y%m%d.log"
                self.addHandler(file_handler)
                file_handler.setFormatter(formatter)

    def _log_with_caller_info(self, level, msg, *args, **kwargs):
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
