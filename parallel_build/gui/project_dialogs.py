from pathlib import Path

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
    QPushButton,
    QVBoxLayout,
)

from parallel_build.config import BuildTarget, Project, ProjectSourceType
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
        build_target_value = [build_target.value for build_target in BuildTarget]
        self.build_target_combobox.addItems(build_target_value)
        self.build_target_combobox.setCurrentIndex(
            build_target_value.index(BuildTarget.webgl)
        )
        main_form.addRow(self.build_target_label, self.build_target_combobox)
        self.build_path_label = QLabel("Build path:")
        self.build_path_textbox = QLineEdit("Builds/WebGL")
        main_form.addRow(self.build_path_label, self.build_path_textbox)

        self.add_button = QPushButton("Add")
        self.add_button.setDefault(True)
        self.cancel_button = QPushButton("Cancel")
        self.button_box = QDialogButtonBox()
        self.button_box.addButton(
            accept_button_text, QDialogButtonBox.ButtonRole.AcceptRole
        )
        self.button_box.addButton("Cancel", QDialogButtonBox.ButtonRole.RejectRole)
        self.button_box.rejected.connect(self.cancel)

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

        layout = QVBoxLayout()
        layout.addLayout(select_source_layout)
        layout.addLayout(main_form)
        layout.addWidget(self.copy_groupbox)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

        self.on_init_end()

    def on_build_path_edit(self):
        pass

    def select_copy_path(self):
        project_path = QFileDialog.getExistingDirectory(self, "Select destination path")
        if project_path == "":
            return
        self.copy_path_textbox.setText(project_path)
        self.has_chosen_copy_path = True

    def generate_project(self):
        post_build_actions = []
        if self.copy_groupbox.isChecked():
            post_build_actions.append(
                {"action": "copy", "params": {"target": self.copy_path_textbox.text()}}
            )
        return Project.model_validate(
            {
                "name": self.project_name_textbox.text(),
                "source": {
                    "type": self.source_type,
                    "value": self.source_value,
                },
                "build": {
                    "target": self.build_target_combobox.currentText(),
                    "path": self.build_path_textbox.text(),
                },
                "post_build": post_build_actions,
            }
        )

    def cancel(self):
        self.close()


class AddNewProjectDialog(ManageProjectDialog):
    def __init__(self, parent):
        super().__init__(parent, "Add new project", "Add")
        self.button_box.accepted.connect(self.add)

    def add(self):
        self.parent().add_project(self.generate_project())
        self.close()


class EditProjectDialog(ManageProjectDialog):
    def __init__(self, parent, project_index: int, project: Project):
        super().__init__(parent, f"Update project {project.name}", "Edit")

        self.project_name_textbox.setText(project.name)
        self.set_source_value(project.source.value)
        self.build_target_combobox.setCurrentText(project.build.target)
        self.build_path_textbox.setText(project.build.path)

        self.copy_groupbox.setChecked(False)
        for action in project.post_build:
            if action.action == "copy":
                self.copy_groupbox.setChecked(True)
                self.copy_path_textbox.setText(action.params["target"])

        self.project_index = project_index
        self.button_box.accepted.connect(self.edit)

    def edit(self):
        self.parent().update_project(self.project_index, self.generate_project())
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
        select_project_path_layout = QVBoxLayout()
        self.project_repository_label = QLabel("Git repository:")
        self.project_repository_textbox = QLineEdit()
        self.project_repository_textbox.setPlaceholderText(
            "git@github.com:gfreeman/black-mesa.git"
        )
        select_project_path_layout.addWidget(self.project_repository_label)
        select_project_path_layout.addWidget(self.project_repository_textbox)
        return select_project_path_layout

    @property
    def source_value(self):
        return self.project_repository_textbox.text()

    def set_source_value(self, value: str):
        self.project_repository_textbox.setText(value)


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
