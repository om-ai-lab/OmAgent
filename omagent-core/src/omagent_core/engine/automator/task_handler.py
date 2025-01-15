import importlib
import logging
import os
from copy import deepcopy
from multiprocessing import (Process, Queue, freeze_support, get_context,
                             set_start_method)
from sys import platform
from typing import List

from omagent_core.engine.automator.task_runner import TaskRunner
from omagent_core.engine.configuration.configuration import Configuration
from omagent_core.engine.configuration.settings.metrics_settings import \
    MetricsSettings
from omagent_core.engine.telemetry.metrics_collector import MetricsCollector
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.container import container
from omagent_core.utils.registry import registry

logger = logging.getLogger(Configuration.get_logging_formatted_name(__name__))

_decorated_functions = {}
_mp_fork_set = False
if not _mp_fork_set:
    try:
        if platform == "win32":
            set_start_method("spawn")
        else:
            set_start_method("fork")
        _mp_fork_set = True
    except Exception as e:
        logger.info(
            f"error when setting multiprocessing.set_start_method - maybe the context is set {e.args}"
        )
    if platform == "darwin":
        os.environ["no_proxy"] = "*"


def register_decorated_fn(
    name: str, poll_interval: int, domain: str, worker_id: str, func
):
    logger.info(f"decorated {name}")
    _decorated_functions[(name, domain)] = {
        "func": func,
        "poll_interval": poll_interval,
        "domain": domain,
        "worker_id": worker_id,
    }


class TaskHandler:
    def __init__(
        self,
        worker_config: List = [],
        workers: List[BaseWorker] = [],
        metrics_settings: MetricsSettings = None,
        import_modules: List[str] = None,
        task_to_domain: dict[str, str] = None,
    ):
        """Initialize a new TaskHandler instance.

        Args:
            worker_config (List): List of worker configurations. Each config should be a dict containing
                worker name, optional concurrency and other settings. The Worker replicates and starts the corresponding number of processes based on the concurrency parameter
            workers (List[BaseWorker]): List of pre-configured worker instances. Instances of these workers are deepcopied based on the concurrency setting.If your worker instances contain objects that cannot be deepcopied, set the instance's concurrency property to 1 and actively expand the concurrency count in the workers list.
            metrics_settings (MetricsSettings, optional): Configuration for metrics collection.
                If None, metrics collection will be disabled.
            import_modules (List[str], optional): List of module paths to import during initialization.
        """

        self.logger_process, self.queue = _setup_logging_queue(
            container.conductor_config
        )

        # imports
        importlib.import_module("omagent_core.engine.http.models.task")
        if import_modules is not None:
            for module in import_modules:
                logger.info(f"loading module {module}")
                importlib.import_module(module)

        existing_workers = []
        for worker in workers:
            concurrency = getattr(
                worker, "concurrency", BaseWorker.model_fields["concurrency"].default
            )
            if concurrency > 1:
                existing_workers.extend(
                    [deepcopy(worker) for _ in range(concurrency - 1)]
                )
        workers.extend(existing_workers)

        for config in worker_config:
            worker_cls = registry.get_worker(config["name"])
            concurrency = config.get(
                "concurrency", BaseWorker.model_fields["concurrency"].default
            )
            workers.extend([worker_cls(**config) for _ in range(concurrency)])
        for worker in workers:
            if task_to_domain is not None:
                task_to_domain[worker.task_definition_name] = worker.domain
        self.__create_task_runner_processes(
            workers, container.conductor_config, metrics_settings
        )
        self.__create_metrics_provider_process(metrics_settings)
        logger.info("TaskHandler initialized")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_processes()

    def stop_processes(self) -> None:
        self.__stop_task_runner_processes()
        self.__stop_metrics_provider_process()
        logger.info("Stopped worker processes...")
        self.queue.put(None)
        self.logger_process.terminate()

    def start_processes(self) -> None:
        logger.info("Starting worker processes...")
        freeze_support()
        self.__start_task_runner_processes()
        self.__start_metrics_provider_process()
        logger.info("Started all processes")

    def join_processes(self) -> None:
        try:
            self.__join_task_runner_processes()
            self.__join_metrics_provider_process()
            logger.info("Joined all processes")
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt: Stopping all processes")
            self.stop_processes()

    def __create_metrics_provider_process(
        self, metrics_settings: MetricsSettings
    ) -> None:
        if metrics_settings is None:
            self.metrics_provider_process = None
            return
        self.metrics_provider_process = Process(
            target=MetricsCollector.provide_metrics, args=(metrics_settings,)
        )
        logger.info("Created MetricsProvider process")

    def __create_task_runner_processes(
        self,
        workers: List[BaseWorker],
        configuration: Configuration,
        metrics_settings: MetricsSettings,
    ) -> None:
        self.task_runner_processes = []
        for worker in workers:
            self.__create_task_runner_process(worker, configuration, metrics_settings)

    def __create_task_runner_process(
        self,
        worker: BaseWorker,
        configuration: Configuration,
        metrics_settings: MetricsSettings,
    ) -> None:
        task_runner = TaskRunner(worker, configuration, metrics_settings)
        process = Process(target=task_runner.run)
        self.task_runner_processes.append(process)

    def __start_metrics_provider_process(self):
        if self.metrics_provider_process is None:
            return
        self.metrics_provider_process.start()
        logger.info("Started MetricsProvider process")

    def __start_task_runner_processes(self):
        n = 0
        for task_runner_process in self.task_runner_processes:
            task_runner_process.start()
            n = n + 1
        logger.info(f"Started {n} TaskRunner process")

    def __join_metrics_provider_process(self):
        if self.metrics_provider_process is None:
            return
        self.metrics_provider_process.join()
        logger.info("Joined MetricsProvider processes")

    def __join_task_runner_processes(self):
        for task_runner_process in self.task_runner_processes:
            task_runner_process.join()
        logger.info("Joined TaskRunner processes")

    def __stop_metrics_provider_process(self):
        self.__stop_process(self.metrics_provider_process)

    def __stop_task_runner_processes(self):
        for task_runner_process in self.task_runner_processes:
            self.__stop_process(task_runner_process)

    def __stop_process(self, process: Process):
        if process is None:
            return
        try:
            logger.debug(f"Terminating process: {process.pid}")
            process.terminate()
        except Exception as e:
            logger.debug(f"Failed to terminate process: {process.pid}, reason: {e}")
            process.kill()
            logger.debug(f"Killed process: {process.pid}")


# Setup centralized logging queue
def _setup_logging_queue(configuration: Configuration):
    queue = Queue()
    if configuration:
        configuration.apply_logging_config()
        log_level = configuration.log_level
        logger_format = configuration.logger_format
    else:
        log_level = logging.DEBUG
        logger_format = None

    logger.setLevel(log_level)

    # start the logger process
    logger_p = Process(target=__logger_process, args=(queue, log_level, logger_format))
    logger_p.start()
    return logger_p, queue


# This process performs the centralized logging
def __logger_process(queue, log_level, logger_format=None):
    c_logger = logging.getLogger(Configuration.get_logging_formatted_name(__name__))

    c_logger.setLevel(log_level)

    # configure a stream handler
    sh = logging.StreamHandler()
    if logger_format:
        formatter = logging.Formatter(logger_format)
        sh.setFormatter(formatter)
    c_logger.addHandler(sh)

    # run forever
    while True:
        # consume a log message, block until one arrives
        message = queue.get()
        # check for shutdown
        if message is None:
            break
        # log the message
        c_logger.handle(message)
