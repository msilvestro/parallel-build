import sys

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from parallel_build.config import Config
from parallel_build.main import build


class BuildWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Parallel Build")

        config = Config.load()

        self.projects_combobox = QComboBox()
        for project in config.projects:
            self.projects_combobox.addItem(project.name)

        self.continuous_checkbox = QCheckBox(text="Continuous build")
        self.continuous_checkbox.setChecked(False)

        self.build_button = QPushButton("Execute")
        self.build_button.pressed.connect(self.start_build_process)

        self.text_area = QPlainTextEdit()
        self.text_area.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(self.projects_combobox)
        layout.addWidget(self.continuous_checkbox)
        layout.addWidget(self.build_button)
        layout.addWidget(self.text_area)

        self.setLayout(layout)

        self.thread = BuildThread(self)
        self.thread.started.connect(self.disable_button)
        self.thread.finished.connect(self.enable_button)

    def enable_button(self):
        self.build_button.setDisabled(False)

    def disable_button(self):
        self.build_button.setDisabled(True)

    @Slot(str)
    def update_text_area(self, message):
        self.text_area.appendPlainText(message)

    def start_build_process(self):
        self.disable_button()
        self.thread.configure(
            self.continuous_checkbox.isChecked(), self.projects_combobox.currentText()
        )
        self.thread.start()


class BuildSignals(QObject):
    build_progress = Signal(str)


class BuildThread(QThread):
    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.signals = BuildSignals()
        self.signals.build_progress.connect(parent.update_text_area)

    def configure(self, continuous, project_name):
        self.continuous = continuous
        self.project_name = project_name

    def run(self):
        for output in build(self.continuous, self.project_name):
            self.signals.build_progress.emit(output)


def show_gui():
    app = QApplication(sys.argv)
    window = BuildWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    show_gui()
