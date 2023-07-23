from parallel_build.command import CommandExecutor


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
    long_message = BuildStepEvent(str)
    short_message = BuildStepEvent(str)
    error = BuildStepEvent(str)
    end = BuildStepEvent(str)
    command_executor = CommandExecutor(
        stdout_function=long_message.emit, stderr_function=error.emit
    )

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

    @classmethod
    @property
    def message(cls):
        class MessageEmitter:
            @staticmethod
            def emit(*args, **kwargs):
                cls.short_message.emit(*args, **kwargs)
                cls.long_message.emit(*args, **kwargs)

        return MessageEmitter
