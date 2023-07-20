class BuildStepEvent:
    def __init__(self, *args, **kwargs):
        self._callbacks = []

    def set(self, *callbacks):
        self._callbacks = callbacks

    def clear(self):
        self._callbacks = []

    def emit(self, *args, **kwargs):
        for callback in self._callbacks:
            callback(*args, **kwargs)


class BuildStep:
    start = BuildStepEvent(str)
    message = BuildStepEvent(str)
    error = BuildStepEvent(str)
    end = BuildStepEvent(str)

    name: str

    @staticmethod
    def start_method(method):
        def _start_method(self, *args, **kwargs):
            self.start.emit(self.name)
            return method(self, *args, **kwargs)

        return _start_method

    @staticmethod
    def end_method(method):
        def _end_method(self, *args, **kwargs):
            output = method(self, *args, **kwargs)
            self.end.emit(self.name)
            return output

        return _end_method
