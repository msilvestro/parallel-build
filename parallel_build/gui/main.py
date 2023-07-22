import sys

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from parallel_build.config import Config, Project, ProjectSourceType
from parallel_build.gui.build_dialog import BuildDialog
from parallel_build.gui.project_dialogs import (
    AddNewGitProjectDialog,
    AddNewLocalProjectDialog,
    EditGitProjectDialog,
    EditLocalProjectDialog,
)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Parallel Build")

        self.config = Config.load()

        self.projects_combobox = QComboBox()
        self.projects_combobox.currentIndexChanged.connect(
            self.on_selected_project_changed
        )

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

        layout = QVBoxLayout()
        layout.addWidget(self.projects_combobox)
        layout.addLayout(projects_buttons_layout)
        layout.addWidget(self.continuous_checkbox)
        layout.addWidget(self.build_button)

        self.setLayout(layout)

        self.update_from_config()

    def update_from_config(self):
        self.projects_combobox.currentIndexChanged.disconnect(
            self.on_selected_project_changed
        )
        projects = [project.name for project in self.config.projects]
        self.projects_combobox.clear()
        self.projects_combobox.addItems(projects)
        self.projects_combobox.setCurrentIndex(self.config.default_project)
        self.projects_combobox.currentIndexChanged.connect(
            self.on_selected_project_changed
        )

        projects_empty = len(projects) == 0
        self.remove_project_button.setEnabled(not projects_empty)
        self.edit_project_button.setEnabled(not projects_empty)
        self.build_button.setEnabled(not projects_empty)

    def start_build_process(self):
        build_dialog = BuildDialog(self)
        build_dialog.start_build_process(
            self.continuous_checkbox.isChecked(), self.projects_combobox.currentText()
        )
        build_dialog.exec()

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
            self.config.default_project -= 1
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

    def on_selected_project_changed(self):
        self.config.default_project = self.projects_combobox.currentIndex()

    def closeEvent(self, event: QCloseEvent):
        self.config.save()


def show_gui():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    show_gui()
