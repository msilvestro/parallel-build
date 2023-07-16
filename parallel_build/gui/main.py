import sys

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from parallel_build.config import Config, Project
from parallel_build.gui.new_project_dialog import NewLocalProjectDialog
from parallel_build.main import build


class BuildWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Parallel Build")
        self.resize(300, 300)

        self.config = Config.load()

        self.projects_combobox = QComboBox()
        self.update_from_config()

        self.add_project_button = QPushButton("Add...")
        self.add_project_button.pressed.connect(self.open_new_project_dialog)
        self.remove_project_button = QPushButton("Remove...")
        self.remove_project_button.pressed.connect(self.remove_project)
        self.edit_project_button = QPushButton("Edit...")
        projects_buttons_layout = QHBoxLayout()
        projects_buttons_layout.addWidget(self.add_project_button)
        projects_buttons_layout.addWidget(self.remove_project_button)
        projects_buttons_layout.addWidget(self.edit_project_button)

        self.continuous_checkbox = QCheckBox(text="Continuous build")
        self.continuous_checkbox.setChecked(False)

        self.build_button = QPushButton("Build")
        self.build_button.pressed.connect(self.start_build_process)

        self.text_area = QPlainTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setFont(QFont("Lucida Console"))

        layout = QVBoxLayout()
        layout.addWidget(self.projects_combobox)
        layout.addLayout(projects_buttons_layout)
        layout.addWidget(self.continuous_checkbox)
        layout.addWidget(self.build_button)
        layout.addWidget(self.text_area)

        self.setLayout(layout)

        self.thread = BuildThread(self)
        self.thread.started.connect(self.disable_button)
        self.thread.finished.connect(self.enable_button)

    def update_from_config(self):
        self.projects_combobox.clear()
        self.projects_combobox.addItems(
            [project.name for project in self.config.projects]
        )

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

    def open_new_project_dialog(self):
        choice, ok = QInputDialog.getItem(
            self,
            "Select project type",
            "Project type:",
            ("Local folder", "Git repository"),
            editable=False,
        )
        if ok:
            match choice:
                case "Local folder":
                    NewLocalProjectDialog(self).exec()

    def add_project(self, project: Project):
        self.config.projects.append(project)
        self.config.save()
        self.update_from_config()
        print(f"Successfully added {project.name}")

    def remove_project(self):
        project_name = self.projects_combobox.currentText()
        reply = QMessageBox.question(
            self,
            "Remove project",
            f"Do you really want to remove {project_name}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            project_to_remove = [
                project
                for project in self.config.projects
                if project.name == project_name
            ][0]
            self.config.projects.remove(project_to_remove)
            self.config.save()
            self.update_from_config()
            print(f"Successfully removed {project_to_remove.name}")


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
