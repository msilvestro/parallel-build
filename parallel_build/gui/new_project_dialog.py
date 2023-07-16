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


class NewProjectDialog(QDialog):
    source_type: ProjectSourceType

    def select_source_layout(self):
        raise NotImplementedError

    @property
    def source_value(self):
        raise NotImplementedError

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add new project")
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
        self.button_box.addButton("Add", QDialogButtonBox.ButtonRole.AcceptRole)
        self.button_box.addButton("Cancel", QDialogButtonBox.ButtonRole.RejectRole)
        self.button_box.accepted.connect(self.add)
        self.button_box.rejected.connect(self.cancel)

        layout = QVBoxLayout()
        layout.addLayout(select_source_layout)
        layout.addLayout(main_form)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def select_project_path(self):
        project_path = Path(
            QFileDialog.getExistingDirectory(self, "Select project path")
        )
        self.project_path_textbox.setText(str(project_path))
        if self.project_name_textbox.text() == "":
            self.project_name_textbox.setText(project_path.name)

    def add(self):
        self.parent().add_project(
            Project.model_validate(
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
        )
        self.close()

    def cancel(self):
        self.close()


class NewLocalProjectDialog(NewProjectDialog):
    source_type = ProjectSourceType.local

    def select_source_layout(self):
        select_project_path_layout = QHBoxLayout()
        self.project_path_textbox = QLineEdit()
        self.project_path_textbox.setPlaceholderText("Select project path...")
        self.project_path_textbox.setReadOnly(True)
        self.select_project_path_button = QPushButton("Choose...")
        self.select_project_path_button.clicked.connect(self.select_project_path)
        select_project_path_layout.addWidget(self.project_path_textbox)
        select_project_path_layout.addWidget(self.select_project_path_button)
        return select_project_path_layout

    @property
    def source_value(self):
        return self.project_path_textbox.text()


class NewGitProjectDialog(NewProjectDialog):
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
