import threading


class AwaitableThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._result = None

    def run(self):
        self._result = self._target(*self._args, **self._kwargs)

    def wait(self):
        self.join()

    def get(self):
        return self._result
