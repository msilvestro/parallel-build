import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Literal


class Source:
    def __init__(self, source_type: Literal["local", "git"], source_value: str):
        source_class = {"local": LocalSource, "git": GitSource}[source_type]
        self.source: LocalSource | GitSource = source_class(source_value)

    def temporary_project(self):
        return self.source.temporary_project()


class LocalSource:
    def __init__(self, value):
        self.project_path = value

    @contextmanager
    def temporary_project(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(self.project_path)
            temp_dir = Path(temp_dir)
            temp_project_path = temp_dir / project_path.name
            shutil.copytree(project_path, temp_project_path)
            yield temp_project_path


class GitSource:
    def __init__(self, value):
        self.git_repository = value

    @contextmanager
    def temporary_project(self):
        raise NotImplementedError
