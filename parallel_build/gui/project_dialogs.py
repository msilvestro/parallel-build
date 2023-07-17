from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
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

        layout = QVBoxLayout()
        layout.addLayout(select_source_layout)
        layout.addLayout(main_form)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

        self.on_init_end()

    def generate_project(self):
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
        self.has_text_been_edited = False
        self.change_project_path()
        self.project_name_textbox.editingFinished.connect(
            self.on_project_name_textbox_edit
        )

    def on_project_name_textbox_edit(self):
        self.has_text_been_edited = True

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
            self.update_project_name_text(
                Path(self.recently_used_combobox.currentText()).name
            )

    def select_project_path(self):
        project_path = Path(
            QFileDialog.getExistingDirectory(self, "Select project path")
        )
        self.project_path_textbox.setText(str(project_path))
        self.update_project_name_text(project_path.name)

    def update_project_name_text(self, new_project_name):
        if not self.has_text_been_edited or self.project_name_textbox.text() == "":
            self.project_name_textbox.setText(new_project_name)

    @property
    def source_value(self):
        if self.is_other_selected:
            return self.project_path_textbox.text()
        return self.recently_used_combobox.currentText()

    def set_source_value(self, value: str):
        self.has_text_been_edited = True
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
    pass


class AddNewGitProjectDialog(GitProjectMixin, AddNewProjectDialog):
    pass


class EditGitProjectDialog(GitProjectMixin, EditProjectDialog):
    pass
