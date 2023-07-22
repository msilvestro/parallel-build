from PySide6.QtCore import QObject, QThread, Signal

from parallel_build.build_step import BuildStep
from parallel_build.main import BuildProcess


class BuildSignals(QObject):
    build_step = Signal(str)
    build_short_progress = Signal(str)
    build_progress = Signal(str)
    build_error = Signal(str)
    build_end = Signal()


class BuildThread(QThread):
    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.signals = BuildSignals()
        self.signals.build_step.connect(parent.on_build_step)
        self.signals.build_short_progress.connect(parent.on_build_short_progress)
        self.signals.build_progress.connect(parent.on_build_progress)
        self.signals.build_error.connect(parent.on_build_error)
        self.signals.build_end.connect(parent.on_build_end)
        self.build_process = None
        self.continuous = False

        BuildStep.start.set(self.signals.build_step.emit)
        BuildStep.short_message.set(self.signals.build_short_progress.emit)
        BuildStep.long_message.set(self.signals.build_progress.emit)
        BuildStep.error.set(self.signals.build_error.emit)

    def configure(self, continuous, project_name):
        self.build_process = BuildProcess(
            project_name=project_name,
            on_build_end=self.signals.build_end.emit,
        )
        self.continuous = continuous

    def run(self):
        self.build_process.run(continuous=self.continuous)

    def stop(self):
        if self.build_process:
            self.build_process.stop()
