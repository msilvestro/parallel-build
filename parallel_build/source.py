import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Literal


class Source:
    def __init__(self, source_type: Literal["local", "git"], source_value: str):
        source_class = {"local": LocalSource, "git": GitSource}[source_type]
        self.source: LocalSource | GitSource = source_class(source_value)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.source.cleanup()
        return None

    def temporary_project(self):
        return self.source.temporary_project()


class LocalSource:
    def __init__(self, value):
        self.project_path = value

    def cleanup(self):
        ...

    @contextmanager
    def temporary_project(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(self.project_path)
            temp_dir = Path(temp_dir)
            temp_project_path = temp_dir / project_path.name
            shutil.copytree(project_path, temp_project_path)
            yield temp_project_path


class GitSource:
    def __init__(self, git_repository):
        self.temp_dir = tempfile.TemporaryDirectory()
        subprocess.run(["git", "clone", git_repository, self.temp_dir.name])
        self.temp_project_path = Path(self.temp_dir.name)

    def cleanup(self):
        self.temp_dir.cleanup()

    @contextmanager
    def temporary_project(self):
        subprocess.run(["git", "pull"], cwd=self.temp_project_path)
        yield self.temp_project_path
