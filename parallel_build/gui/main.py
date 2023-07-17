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

from parallel_build.config import Config, Project, ProjectSourceType
from parallel_build.gui.project_dialogs import (
    AddNewGitProjectDialog,
    AddNewLocalProjectDialog,
    EditGitProjectDialog,
    EditLocalProjectDialog,
)
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
        self.edit_project_button.pressed.connect(self.open_edit_project_dialog)
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
                    AddNewLocalProjectDialog(self).exec()
                case "Git repository":
                    AddNewGitProjectDialog(self).exec()

    def add_project(self, project: Project):
        self.config.projects.append(project)
        self.config.save()
        self.update_from_config()
        self.projects_combobox.setCurrentIndex(self.config.projects.index(project))
        print(f"Successfully added {project.name}")

    def remove_project(self):
        project_to_remove = self.config.projects[self.projects_combobox.currentIndex()]
        reply = QMessageBox.question(
            self,
            "Remove project",
            f"Do you really want to remove {project_to_remove.name}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.config.projects.remove(project_to_remove)
            self.config.save()
            self.update_from_config()
            print(f"Successfully removed {project_to_remove.name}")

    def open_edit_project_dialog(self):
        project_index = self.projects_combobox.currentIndex()
        project_to_update = self.config.projects[project_index]
        match project_to_update.source.type:
            case ProjectSourceType.local:
                EditLocalProjectDialog(self, project_index, project_to_update).exec()
            case ProjectSourceType.git:
                EditGitProjectDialog(self, project_index, project_to_update).exec()

    def update_project(self, project_to_update_index: int, updated_project: Project):
        self.config.projects[project_to_update_index] = updated_project
        self.config.save()
        self.update_from_config()
        self.projects_combobox.setCurrentIndex(project_to_update_index)
        print(f"Successfully updated {updated_project.name}")


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
