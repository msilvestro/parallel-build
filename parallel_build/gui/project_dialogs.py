import subprocess
from pathlib import Path

import msgspec
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from parallel_build.config import BuildTarget, Project, ProjectSourceType
from parallel_build.unity_builder import validate_unity_project
from parallel_build.unity_hub import UnityRecentlyUsedProjects


class ManageProjectDialog(QDialog):
    source_type: ProjectSourceType

    def select_source_layout(self):
        raise NotImplementedError

    @property
    def source_value(self):
        raise NotImplementedError

    def set_source_value(self, value: str):
        raise NotImplementedError

    def on_init_end(self):
        pass

    def __init__(self, parent, window_title: str, accept_button_text: str):
        super().__init__(parent)
        self.setWindowTitle(window_title)
        self.setMinimumWidth(300)

        select_source_layout = self.select_source_layout()

        main_form = QFormLayout()
        self.project_name_label = QLabel("Project name:")
        self.project_name_textbox = QLineEdit()
        main_form.addRow(self.project_name_label, self.project_name_textbox)
        self.build_target_label = QLabel("Build target:")
        self.build_target_combobox = QComboBox()
        self.build_targets = [build_target for build_target in BuildTarget]
        self.build_target_combobox.addItems(self.build_targets)
        self.build_target_combobox.setCurrentIndex(
            self.build_targets.index(BuildTarget.webgl)
        )
        self.build_target_combobox.currentIndexChanged.connect(
            self.on_build_target_change
        )
        main_form.addRow(self.build_target_label, self.build_target_combobox)
        self.build_method_label = QLabel("Build method:")
        self.build_method_textbox = QLineEdit()
        self.build_method_textbox.setEnabled(False)
        main_form.addRow(self.build_method_label, self.build_method_textbox)
        self.build_path_label = QLabel("Build path:")
        self.build_path_textbox = QLineEdit("Builds/WebGL")
        main_form.addRow(self.build_path_label, self.build_path_textbox)

        self.copy_groupbox = QGroupBox("Copy build to destination folder")
        self.copy_groupbox.setCheckable(True)
        self.copy_groupbox.setChecked(True)
        select_path_layout = QHBoxLayout()
        self.copy_path_textbox = QLineEdit()
        self.copy_path_textbox.setPlaceholderText("Select destination folder...")
        self.copy_path_textbox.setReadOnly(True)
        choose_button = QPushButton("Choose...")
        choose_button.clicked.connect(self.select_copy_path)
        self.has_chosen_copy_path = False
        select_path_layout.addWidget(self.copy_path_textbox)
        select_path_layout.addWidget(choose_button)
        self.copy_groupbox.setLayout(select_path_layout)

        self.itch_groupbox = QGroupBox("Publish to itch.io")
        self.itch_groupbox.setCheckable(True)
        self.itch_groupbox.setChecked(False)
        itch_groupbox_layout = QFormLayout()
        self.itch_user_textbox = QLineEdit()
        self.itch_user_textbox.setPlaceholderText("gfreeman")
        itch_groupbox_layout.addRow(QLabel("Itch user:"), self.itch_user_textbox)
        self.itch_game_textbox = QLineEdit()
        self.itch_game_textbox.setPlaceholderText("black-mesa")
        itch_groupbox_layout.addRow(QLabel("Itch game:"), self.itch_game_textbox)
        self.itch_channel_textbox = QLineEdit()
        self.itch_channel_textbox.setPlaceholderText("webgl")
        itch_groupbox_layout.addRow(QLabel("Itch channel:"), self.itch_channel_textbox)
        self.itch_groupbox.setLayout(itch_groupbox_layout)

        self.button_box = QDialogButtonBox()
        self.button_box.addButton(
            accept_button_text, QDialogButtonBox.ButtonRole.AcceptRole
        )
        self.button_box.addButton("Cancel", QDialogButtonBox.ButtonRole.RejectRole)
        self.button_box.rejected.connect(self.cancel)

        layout = QVBoxLayout()
        layout.addLayout(select_source_layout)
        layout.addLayout(main_form)
        layout.addWidget(self.copy_groupbox)
        layout.addWidget(self.itch_groupbox)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

        self.on_init_end()

    def select_copy_path(self):
        project_path = QFileDialog.getExistingDirectory(self, "Select destination path")
        if project_path == "":
            return
        self.copy_path_textbox.setText(project_path)
        self.has_chosen_copy_path = True

    def show_validation_error(self, message: str):
        messagebox = QMessageBox()
        messagebox.setWindowTitle("Validation error")
        messagebox.setIcon(QMessageBox.Icon.Warning)
        messagebox.setText(message)
        messagebox.exec()

    def generate_project(self):
        if self.source_value == "":
            self.show_validation_error(
                f"{self.source_type.pretty_name} cannot be empty"
            )
            return False

        if self.source_type == ProjectSourceType.local and not validate_unity_project(
            Path(self.source_value)
        ):
            self.show_validation_error(
                f"{self.source_value} is not a valid Unity project"
            )
            return False

        project_name = self.project_name_textbox.text()
        if project_name == "":
            self.show_validation_error("Project name cannot be empty")
            return False

        post_build_actions = []
        if self.copy_groupbox.isChecked():
            post_build_actions.append(
                {"action": "copy", "params": {"target": self.copy_path_textbox.text()}}
            )
        if self.itch_groupbox.isChecked():
            itch_user = self.itch_user_textbox.text()
            itch_game = self.itch_game_textbox.text()
            itch_channel = self.itch_channel_textbox.text()
            if itch_user == "" or itch_game == "" or itch_channel == "":
                self.show_validation_error(
                    "No empty value allowed for itch.io parameters"
                )
                return False

            post_build_actions.append(
                {
                    "action": "publish-itch",
                    "params": {
                        "itch_user": itch_user,
                        "itch_game": itch_game,
                        "itch_channel": itch_channel,
                    },
                }
            )
        try:
            return msgspec.convert(
                {
                    "name": project_name,
                    "source": {
                        "type": self.source_type,
                        "value": self.source_value,
                    },
                    "build": {
                        "target": self.build_target_combobox.currentText(),
                        "method": self.build_method_textbox.text(),
                        "path": self.build_path_textbox.text(),
                    },
                    "post_build": post_build_actions,
                },
                type=Project,
            )
        except msgspec.ValidationError as e:
            self.show_validation_error(str(e))
            return False

    def cancel(self):
        self.close()

    def on_build_target_change(self):
        self.build_method_textbox.setEnabled(
            self.build_target_combobox.currentIndex()
            == self.build_targets.index(BuildTarget.custom)
        )


class AddNewProjectDialog(ManageProjectDialog):
    def __init__(self, parent):
        super().__init__(parent, "Add new project", "Add")
        self.button_box.accepted.connect(self.add)

    def add(self):
        project = self.generate_project()
        if not project:
            return
        self.parent().add_project(project)
        self.close()


class EditProjectDialog(ManageProjectDialog):
    def __init__(self, parent, project_index: int, project: Project):
        super().__init__(parent, f"Update project {project.name}", "Save")

        self.project_name_textbox.setText(project.name)
        self.set_source_value(project.source.value)
        self.build_target_combobox.setCurrentText(project.build.target)
        self.build_method_textbox.setText(project.build.method)
        self.build_path_textbox.setText(project.build.path)

        self.copy_groupbox.setChecked(False)
        self.itch_groupbox.setChecked(False)
        for action in project.post_build:
            if action.action == "copy":
                self.copy_groupbox.setChecked(True)
                self.copy_path_textbox.setText(action.params["target"])
            elif action.action == "publish-itch":
                self.itch_groupbox.setChecked(True)
                self.itch_user_textbox.setText(action.params["itch_user"])
                self.itch_game_textbox.setText(action.params["itch_game"])
                self.itch_channel_textbox.setText(action.params["itch_channel"])

        self.project_index = project_index
        self.button_box.accepted.connect(self.edit)

    def edit(self):
        project = self.generate_project()
        if not project:
            return
        self.parent().update_project(self.project_index, project)
        self.close()


class LocalProjectMixin:
    source_type = ProjectSourceType.local

    def select_source_layout(self):
        self.recently_used_projects = UnityRecentlyUsedProjects().get()
        self.recently_used_combobox = QComboBox()
        self.recently_used_combobox.addItems(self.recently_used_projects)
        self.recently_used_combobox.addItem("Other path...")
        self.recently_used_combobox.currentIndexChanged.connect(
            self.change_project_path
        )

        select_project_path_layout = QHBoxLayout()
        self.project_path_textbox = QLineEdit()
        self.project_path_textbox.setPlaceholderText("Select project path...")
        self.project_path_textbox.setReadOnly(True)
        self.select_project_path_button = QPushButton("Choose...")
        self.select_project_path_button.clicked.connect(self.select_project_path)
        select_project_path_layout.addWidget(self.project_path_textbox)
        select_project_path_layout.addWidget(self.select_project_path_button)

        layout = QVBoxLayout()
        layout.addWidget(self.recently_used_combobox)
        layout.addLayout(select_project_path_layout)

        return layout

    def on_init_end(self):
        self.has_project_path_been_edited = False
        self.change_project_path()
        self.project_name_textbox.editingFinished.connect(
            self.on_project_name_textbox_edit
        )
        self.build_path_textbox.editingFinished.connect(self.update_copy_groupbox)

    def on_project_name_textbox_edit(self):
        self.has_project_path_been_edited = True

    @property
    def is_other_selected(self):
        return (
            self.recently_used_combobox.currentIndex()
            == self.recently_used_combobox.count() - 1
        )

    def change_project_path(self):
        self.project_path_textbox.setEnabled(self.is_other_selected)
        self.select_project_path_button.setEnabled(self.is_other_selected)
        if not self.is_other_selected:
            self.on_project_path_update()

    def select_project_path(self):
        project_path = QFileDialog.getExistingDirectory(self, "Select project path")
        if project_path == "":
            return

        self.project_path_textbox.setText(project_path)
        self.on_project_path_update()

    @property
    def selected_project_path(self):
        if self.is_other_selected:
            return Path(self.project_path_textbox.text())
        return Path(self.recently_used_combobox.currentText())

    def on_project_path_update(self):
        if (
            not self.has_project_path_been_edited
            or self.project_name_textbox.text() == ""
        ):
            self.project_name_textbox.setText(self.selected_project_path.name)
        self.update_copy_groupbox()

    def update_copy_groupbox(self):
        if self.copy_groupbox.isChecked() and (
            not self.has_chosen_copy_path or self.copy_path_textbox.text() == ""
        ):
            self.copy_path_textbox.setText(
                str(self.selected_project_path / self.build_path_textbox.text())
            )

    @property
    def source_value(self):
        if self.is_other_selected:
            return self.project_path_textbox.text()
        return self.recently_used_combobox.currentText()

    def set_source_value(self, value: str):
        self.has_project_path_been_edited = True
        if value in self.recently_used_projects:
            self.recently_used_combobox.setCurrentIndex(
                self.recently_used_projects.index(value)
            )
            return
        self.recently_used_combobox.setCurrentIndex(
            self.recently_used_combobox.count() - 1
        )
        self.project_path_textbox.setText(value)


class GitProjectMixin:
    source_type = ProjectSourceType.git

    def select_source_layout(self):
        select_project_repository_layout = QVBoxLayout()
        self.project_repository_label = QLabel("Git repository:")
        project_repository_value_layout = QHBoxLayout()
        self.project_repository_textbox = QLineEdit()
        self.project_repository_textbox.setPlaceholderText(
            "git@github.com:gfreeman/black-mesa.git"
        )
        self.project_repository_check_button = QPushButton("Check")
        self.project_repository_check_button.pressed.connect(
            self.check_valid_repository
        )
        project_repository_value_layout.addWidget(self.project_repository_textbox)
        project_repository_value_layout.addWidget(self.project_repository_check_button)
        select_project_repository_layout.addWidget(self.project_repository_label)
        select_project_repository_layout.addLayout(project_repository_value_layout)
        return select_project_repository_layout

    @property
    def source_value(self):
        return self.project_repository_textbox.text()

    def set_source_value(self, value: str):
        self.project_repository_textbox.setText(value)

    def check_valid_repository(self):
        valid_repository = (
            subprocess.run(f"git ls-remote -h {self.source_value}").returncode == 0
        )

        messagebox = QMessageBox()
        messagebox.setWindowTitle("Project repository")
        messagebox.setIcon(
            QMessageBox.Icon.Information
            if valid_repository
            else QMessageBox.Icon.Warning
        )
        messagebox.setText(
            f"{self.source_value} is a valid repository"
            if valid_repository
            else f"{self.source_value} is not a valid repository"
        )
        messagebox.exec()


class AddNewLocalProjectDialog(LocalProjectMixin, AddNewProjectDialog):
    pass


class EditLocalProjectDialog(LocalProjectMixin, EditProjectDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_project_path_been_edited = True
        self.has_chosen_copy_path = True


class AddNewGitProjectDialog(GitProjectMixin, AddNewProjectDialog):
    pass


class EditGitProjectDialog(GitProjectMixin, EditProjectDialog):
    pass
