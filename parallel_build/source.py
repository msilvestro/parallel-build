import shutil
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

from parallel_build.build_step import BuildStep
from parallel_build.config import ProjectSourceType
from parallel_build.utils import run_subprocess


def get_source(
    project_name: str,
    source_type: ProjectSourceType,
    source_value: str,
    git_polling_interval: int,
):
    if source_type == ProjectSourceType.local:
        return LocalSource(project_name, source_value)
    elif source_type == ProjectSourceType.git:
        return GitSource(project_name, source_value, git_polling_interval)


def ignore_patterns(project_path: Path):
    def _ignore_patterns(path, names):
        if Path(path) in (project_path / "Temp", project_path / "Logs"):
            return names
        return []

    return _ignore_patterns


class Interrupt(Exception):
    """Interrupt copy operation."""


class LocalSource(BuildStep):
    name = "Pre build: local source"

    def __init__(self, project_name: str, project_path: str, verbose: bool = False):
        self.project_name = project_name
        self.project_path = Path(project_path)
        self.interrupt = False
        self.verbose = verbose

    @BuildStep.start_method
    def __enter__(self):
        return self

    @BuildStep.end_method
    def __exit__(self, exc_type, exc_value, traceback):
        return None

    def interruptable_copy(self, src, dst, *, follow_symlinks=True):
        if self.interrupt:
            raise Interrupt("Interrupting copy operation")
        if self.verbose:
            self.message.emit(f"Copying {src} to {dst}")
        return shutil.copy2(src, dst, follow_symlinks=True)

    @contextmanager
    def temporary_project(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            self.message.emit(f"Copying {self.project_name} files to {temp_dir}...")
            temp_dir = Path(temp_dir)
            temp_project_path = temp_dir / self.project_name
            try:
                shutil.copytree(
                    self.project_path,
                    temp_project_path,
                    copy_function=self.interruptable_copy,
                    ignore=ignore_patterns(self.project_path),
                )
            except Interrupt:
                self.message.emit("Project files copy stopped")
                pass
            yield temp_project_path

    def stop(self):
        self.interrupt = True


class GitSource(BuildStep):
    name = "Pre build: git source"

    def __init__(
        self, project_name: str, git_repository: str, git_polling_interval: int = 30
    ):
        self.project_name = project_name
        self.git_repository = git_repository
        self.git_polling_interval = git_polling_interval

        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.temp_project_path = Path(self.temp_dir.name) / project_name
        self.build_count = 0
        self.interrupt = False

    @BuildStep.start_method
    def __enter__(self):
        self.temp_project_path.mkdir()
        self.message.emit(f"Cloning {self.project_name} to {self.temp_project_path}...")
        # strange: it seems like part of the output of git clone is sent to stderr
        run_subprocess(["git", "clone", self.git_repository, self.temp_project_path])
        return self

    @BuildStep.end_method
    def __exit__(self, exc_type, exc_value, traceback):
        self.temp_dir.cleanup()

    @contextmanager
    def temporary_project(self):
        previous_commit = run_subprocess(
            ["git", "rev-parse", "HEAD"], cwd=self.temp_project_path
        )
        while self.build_count > 0 and not self.interrupt:
            self.message.emit(
                run_subprocess(["git", "pull"], cwd=self.temp_project_path)
            )
            current_commit = run_subprocess(
                ["git", "rev-parse", "HEAD"], cwd=self.temp_project_path
            )
            if current_commit != previous_commit or self.interrupt:
                break
            self.message.emit(
                f"No new changes, waiting {self.git_polling_interval} seconds..."
            )
            for i in range(self.git_polling_interval):
                if self.interrupt:
                    break
                time.sleep(1)

        yield self.temp_project_path
        self.build_count += 1

    def stop(self):
        self.interrupt = True
