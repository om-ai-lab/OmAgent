import logging
import os
import time
from typing import Any, Dict, List

from omagent_core.engine.configuration.configuration import Configuration
from omagent_core.engine.configuration.settings.metrics_settings import \
    MetricsSettings
from omagent_core.engine.telemetry.model.metric_documentation import \
    MetricDocumentation
from omagent_core.engine.telemetry.model.metric_label import MetricLabel
from omagent_core.engine.telemetry.model.metric_name import MetricName
from prometheus_client import (CollectorRegistry, Counter, Gauge,
                               write_to_textfile)
from prometheus_client.multiprocess import MultiProcessCollector

logger = logging.getLogger(Configuration.get_logging_formatted_name(__name__))


class MetricsCollector:
    counters = {}
    gauges = {}
    registry = CollectorRegistry()
    must_collect_metrics = False

    def __init__(self, settings: MetricsSettings):
        if settings != None:
            os.environ["PROMETHEUS_MULTIPROC_DIR"] = settings.directory
            MultiProcessCollector(self.registry)
            self.must_collect_metrics = True

    @staticmethod
    def provide_metrics(settings: MetricsSettings) -> None:
        if settings == None:
            return
        OUTPUT_FILE_PATH = os.path.join(settings.directory, settings.file_name)
        registry = CollectorRegistry()
        MultiProcessCollector(registry)
        while True:
            write_to_textfile(OUTPUT_FILE_PATH, registry)
            time.sleep(settings.update_interval)

    def increment_task_poll(self, task_type: str) -> None:
        self.__increment_counter(
            name=MetricName.TASK_POLL,
            documentation=MetricDocumentation.TASK_POLL,
            labels={MetricLabel.TASK_TYPE: task_type},
        )

    def increment_task_execution_queue_full(self, task_type: str) -> None:
        self.__increment_counter(
            name=MetricName.TASK_EXECUTION_QUEUE_FULL,
            documentation=MetricDocumentation.TASK_EXECUTION_QUEUE_FULL,
            labels={MetricLabel.TASK_TYPE: task_type},
        )

    def increment_uncaught_exception(self):
        self.__increment_counter(
            name=MetricName.THREAD_UNCAUGHT_EXCEPTION,
            documentation=MetricDocumentation.THREAD_UNCAUGHT_EXCEPTION,
            labels={},
        )

    def increment_task_poll_error(self, task_type: str, exception: Exception) -> None:
        self.__increment_counter(
            name=MetricName.TASK_POLL_ERROR,
            documentation=MetricDocumentation.TASK_POLL_ERROR,
            labels={
                MetricLabel.TASK_TYPE: task_type,
                MetricLabel.EXCEPTION: str(exception),
            },
        )

    def increment_task_paused(self, task_type: str) -> None:
        self.__increment_counter(
            name=MetricName.TASK_PAUSED,
            documentation=MetricDocumentation.TASK_PAUSED,
            labels={MetricLabel.TASK_TYPE: task_type},
        )

    def increment_task_execution_error(
        self, task_type: str, exception: Exception
    ) -> None:
        self.__increment_counter(
            name=MetricName.TASK_EXECUTE_ERROR,
            documentation=MetricDocumentation.TASK_EXECUTE_ERROR,
            labels={
                MetricLabel.TASK_TYPE: task_type,
                MetricLabel.EXCEPTION: str(exception),
            },
        )

    def increment_task_ack_failed(self, task_type: str) -> None:
        self.__increment_counter(
            name=MetricName.TASK_ACK_FAILED,
            documentation=MetricDocumentation.TASK_ACK_FAILED,
            labels={MetricLabel.TASK_TYPE: task_type},
        )

    def increment_task_ack_error(self, task_type: str, exception: Exception) -> None:
        self.__increment_counter(
            name=MetricName.TASK_ACK_ERROR,
            documentation=MetricDocumentation.TASK_ACK_ERROR,
            labels={
                MetricLabel.TASK_TYPE: task_type,
                MetricLabel.EXCEPTION: str(exception),
            },
        )

    def increment_task_update_error(self, task_type: str, exception: Exception) -> None:
        self.__increment_counter(
            name=MetricName.TASK_UPDATE_ERROR,
            documentation=MetricDocumentation.TASK_UPDATE_ERROR,
            labels={
                MetricLabel.TASK_TYPE: task_type,
                MetricLabel.EXCEPTION: str(exception),
            },
        )

    def increment_external_payload_used(
        self, entity_name: str, operation: str, payload_type: str
    ) -> None:
        self.__increment_counter(
            name=MetricName.EXTERNAL_PAYLOAD_USED,
            documentation=MetricDocumentation.EXTERNAL_PAYLOAD_USED,
            labels={
                MetricLabel.ENTITY_NAME: entity_name,
                MetricLabel.OPERATION: operation,
                MetricLabel.PAYLOAD_TYPE: payload_type,
            },
        )

    def increment_workflow_start_error(
        self, workflow_type: str, exception: Exception
    ) -> None:
        self.__increment_counter(
            name=MetricName.WORKFLOW_START_ERROR,
            documentation=MetricDocumentation.WORKFLOW_START_ERROR,
            labels={
                MetricLabel.WORKFLOW_TYPE: workflow_type,
                MetricLabel.EXCEPTION: str(exception),
            },
        )

    def record_workflow_input_payload_size(
        self, workflow_type: str, version: str, payload_size: int
    ) -> None:
        self.__record_gauge(
            name=MetricName.WORKFLOW_INPUT_SIZE,
            documentation=MetricDocumentation.WORKFLOW_INPUT_SIZE,
            labels={
                MetricLabel.WORKFLOW_TYPE: workflow_type,
                MetricLabel.WORKFLOW_VERSION: version,
            },
            value=payload_size,
        )

    def record_task_result_payload_size(
        self, task_type: str, payload_size: int
    ) -> None:
        self.__record_gauge(
            name=MetricName.TASK_RESULT_SIZE,
            documentation=MetricDocumentation.TASK_RESULT_SIZE,
            labels={MetricLabel.TASK_TYPE: task_type},
            value=payload_size,
        )

    def record_task_poll_time(self, task_type: str, time_spent: float) -> None:
        self.__record_gauge(
            name=MetricName.TASK_POLL_TIME,
            documentation=MetricDocumentation.TASK_POLL_TIME,
            labels={MetricLabel.TASK_TYPE: task_type},
            value=time_spent,
        )

    def record_task_execute_time(self, task_type: str, time_spent: float) -> None:
        self.__record_gauge(
            name=MetricName.TASK_EXECUTE_TIME,
            documentation=MetricDocumentation.TASK_EXECUTE_TIME,
            labels={MetricLabel.TASK_TYPE: task_type},
            value=time_spent,
        )

    def __increment_counter(
        self,
        name: MetricName,
        documentation: MetricDocumentation,
        labels: Dict[MetricLabel, str],
    ) -> None:
        if not self.must_collect_metrics:
            return
        counter = self.__get_counter(
            name=name, documentation=documentation, labelnames=labels.keys()
        )
        counter.labels(*labels.values()).inc()

    def __record_gauge(
        self,
        name: MetricName,
        documentation: MetricDocumentation,
        labels: Dict[MetricLabel, str],
        value: Any,
    ) -> None:
        if not self.must_collect_metrics:
            return
        gauge = self.__get_gauge(
            name=name, documentation=documentation, labelnames=labels.keys()
        )
        gauge.labels(*labels.values()).set(value)

    def __get_counter(
        self,
        name: MetricName,
        documentation: MetricDocumentation,
        labelnames: List[MetricLabel],
    ) -> Counter:
        if name not in self.counters:
            self.counters[name] = self.__generate_counter(
                name, documentation, labelnames
            )
        return self.counters[name]

    def __get_gauge(
        self,
        name: MetricName,
        documentation: MetricDocumentation,
        labelnames: List[MetricLabel],
    ) -> Gauge:
        if name not in self.gauges:
            self.gauges[name] = self.__generate_gauge(name, documentation, labelnames)
        return self.gauges[name]

    def __generate_counter(
        self,
        name: MetricName,
        documentation: MetricDocumentation,
        labelnames: List[MetricLabel],
    ) -> Counter:
        return Counter(
            name=name,
            documentation=documentation,
            labelnames=labelnames,
            registry=self.registry,
        )

    def __generate_gauge(
        self,
        name: MetricName,
        documentation: MetricDocumentation,
        labelnames: List[MetricLabel],
    ) -> Gauge:
        return Gauge(
            name=name,
            documentation=documentation,
            labelnames=labelnames,
            registry=self.registry,
        )
