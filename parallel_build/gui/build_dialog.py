import time
from threading import Thread

from PySide6.QtCore import Slot
from PySide6.QtGui import QCloseEvent, QFont
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from parallel_build.gui.build_thread import BuildThread
from parallel_build.gui.elided_label import QElidedLabel
from parallel_build.utils import OperatingSystem

RED_COLOR = "#ef4e40"


class BuildDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Build")
        self.resize(500, 250)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)

        self.build_step_label = QLabel("Build in progress")
        self.build_step_label.setStyleSheet("font-weight: bold;")
        self.build_message_label = QElidedLabel()
        labels_layout = QHBoxLayout()
        labels_layout.addWidget(self.build_step_label, stretch=0)
        labels_layout.addWidget(self.build_message_label, stretch=1)

        self.output_text_area = QTextEdit()
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

        self.should_close = False

    def append_output_text(
        self,
        text: str,
        bold: bool = False,
        color: str | None = None,
        add_space_before: bool = False,
    ):
        text = text.replace("\n", "<br />")
        if bold:
            text = f"<b>{text}</b>"
        if color:
            text = f"<span style='color: {color};'>{text}</span>"
        if add_space_before:
            text = f"<br />{text}"
        self.output_text_area.append(text)

    def start_build_process(self, continuous: bool, project_name: str):
        self.thread.configure(continuous, project_name)
        self.thread.start()

    def on_build_start(self):
        self.output_text_area.clear()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)

    def on_thread_end(self):
        if self.should_close:
            self.close()
            return
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(100)
        self.cancel_button.setText("Close")

    def on_build_end(self, finished_with_success: bool):
        self.on_thread_end()
        if finished_with_success:
            self.build_step_label.setText("Finished successfully!")
            self.build_message_label.setText("")

    def update_build_message_label_text(self, text: str):
        self.build_message_label.setText(" ".join(text.strip().split()))

    @Slot(str)
    def on_build_step(self, build_step_name: str):
        if self.should_close:
            return
        self.build_step_label.setText(build_step_name)
        self.append_output_text(
            f"// {build_step_name}",
            bold=True,
            add_space_before=self.output_text_area.toPlainText() != "",
        )

    @Slot(str)
    def on_build_short_progress(self, short_message: str):
        if self.should_close:
            return
        self.update_build_message_label_text(short_message.strip())

    @Slot(str)
    def on_build_progress(self, message: str):
        if self.should_close:
            return
        self.append_output_text(message)

    @Slot(str)
    def on_build_error(self, error_message: str):
        if self.should_close:
            return
        self.append_output_text(error_message, color=RED_COLOR)
        self.update_build_message_label_text(error_message.strip())
        self.build_message_label.setStyleSheet(f"color: {RED_COLOR};")

    def cancel(self):
        self.close()

    def closeEvent(self, event: QCloseEvent):
        if self.thread.isFinished():
            return

        if self.should_close:
            # force close
            self.thread.stop()
            return

        self.thread.stop()
        if OperatingSystem.current == OperatingSystem.macos:
            # MacOS seems to have issues with closing the Unity build process
            Thread(target=self.close_thread_with_retries).start()
        self.build_message_label.setText("Please wait while stopping build process...")
        self.should_close = True
        event.setAccepted(False)

    def close_thread_with_retries(self):
        attempts_delay = [1, 5, 15]
        for i, attempt_delay in enumerate(attempts_delay):
            for _ in range(attempt_delay):
                time.sleep(1)
                if self.thread.isFinished():
                    return
            print(f"Attempt #{i+1} at stopping the build process")
            self.thread.stop()
