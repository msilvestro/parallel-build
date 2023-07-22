from PySide6.QtCore import Slot
from PySide6.QtGui import QCloseEvent, QFont
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from parallel_build.gui.build_thread import BuildThread
from parallel_build.gui.elided_label import QElidedLabel
from parallel_build.utils import OperatingSystem


class BuildDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Build")
        self.resize(500, 200)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)

        self.build_step_label = QLabel("Build in progress")
        self.build_step_label.setStyleSheet("font-weight: bold;")
        self.build_message_label = QElidedLabel()
        labels_layout = QHBoxLayout()
        labels_layout.addWidget(self.build_step_label, stretch=0)
        labels_layout.addWidget(self.build_message_label, stretch=1)

        self.output_text_area = QPlainTextEdit()
        self.output_text_area.setReadOnly(True)
        self.output_text_area.setFont(QFont(OperatingSystem.monospace_font))

        self.button_box = QDialogButtonBox()
        self.cancel_button = QPushButton("Cancel")
        self.button_box.addButton(
            self.cancel_button, QDialogButtonBox.ButtonRole.RejectRole
        )
        self.button_box.rejected.connect(self.cancel)

        layout = QVBoxLayout()
        layout.addWidget(self.progress_bar)
        layout.addLayout(labels_layout)
        layout.addWidget(self.output_text_area)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

        self.thread = BuildThread(self)
        self.thread.started.connect(self.on_build_start)
        self.thread.finished.connect(self.on_thread_end)

    def start_build_process(self, continuous: bool, project_name: str):
        self.thread.configure(continuous, project_name)
        self.thread.start()

    def on_build_start(self):
        self.output_text_area.clear()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)

    def on_thread_end(self):
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(100)
        self.cancel_button.setText("Close")

    def on_build_end(self, with_error: bool):
        self.on_thread_end()
        if not with_error:
            self.build_step_label.setText("Finished successfully!")
            self.build_message_label.setText("")

    @Slot(str)
    def on_build_step(self, build_step_name: str):
        self.build_step_label.setText(build_step_name)
        self.build_message_label.setText("")
        self.output_text_area.appendPlainText(f"\n// {build_step_name}")

    @Slot(str)
    def on_build_short_progress(self, short_message: str):
        self.build_message_label.setText(short_message.strip())

    @Slot(str)
    def on_build_progress(self, message: str):
        self.output_text_area.appendPlainText(message)

    @Slot(str)
    def on_build_error(self, error_message: str):
        self.output_text_area.appendPlainText(error_message)
        self.build_message_label.setText(error_message.strip())
        self.build_message_label.setStyleSheet("color: red;")

    def cancel(self):
        self.close()

    def closeEvent(self, event: QCloseEvent):
        self.thread.stop()
