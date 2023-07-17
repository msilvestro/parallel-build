import shutil
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

from parallel_build.config import ProjectSourceType
from parallel_build.utils import run_subprocess


class Source:
    def __init__(
        self,
        project_name: str,
        source_type: ProjectSourceType,
        source_value: str,
        **kwargs: dict,
    ):
        source_class = {
            ProjectSourceType.local: LocalSource,
            ProjectSourceType.git: GitSource,
        }[source_type]
        self.source: LocalSource | GitSource = source_class(
            project_name, source_value, **kwargs
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.source.cleanup()
        return None

    def temporary_project(self):
        return self.source.temporary_project()


def ignore_patterns(project_path: Path):
    def _ignore_patterns(path, names):
        if Path(path) in (project_path / "Temp", project_path / "Logs"):
            return names
        return []

    return _ignore_patterns


class LocalSource:
    def __init__(self, project_name: str, project_path: str, **kwargs):
        self.project_name = project_name
        self.project_path = Path(project_path)

    def cleanup(self):
        ...

    @contextmanager
    def temporary_project(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_dir = Path(temp_dir)
            temp_project_path = temp_dir / self.project_name
            shutil.copytree(
                self.project_path,
                temp_project_path,
                ignore=ignore_patterns(self.project_path),
            )
            yield temp_project_path


class GitSource:
    def __init__(self, project_name: str, git_repository: str, **kwargs):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.temp_project_path = Path(self.temp_dir.name) / project_name
        self.temp_project_path.mkdir()
        run_subprocess(["git", "clone", git_repository, self.temp_project_path])
        self.build_count = 0
        self.git_polling_interval = kwargs.get("git_polling_interval", 30)

    def cleanup(self):
        self.temp_dir.cleanup()

    @contextmanager
    def temporary_project(self):
        previous_commit = run_subprocess(
            ["git", "rev-parse", "HEAD"], cwd=self.temp_project_path
        )
        while self.build_count > 0:
            run_subprocess(["git", "pull"], cwd=self.temp_project_path)
            current_commit = run_subprocess(
                ["git", "rev-parse", "HEAD"], cwd=self.temp_project_path
            )
            if current_commit != previous_commit:
                break
            print(f"No new changes, waiting {self.git_polling_interval} seconds...")
            time.sleep(self.git_polling_interval)

        yield self.temp_project_path
        self.build_count += 1
