class QueueWorkerConfiguration:
    def __init__(self):
        self.configuration = {}

    def add_configuration(self, key: str, value: str) -> None:
        self.configuration[key] = value
