import os
import shutil
import tempfile
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

from parallel_build.build_step import BuildStep
from parallel_build.config import ProjectSourceType
from parallel_build.exceptions import BuildProcessError, BuildProcessInterrupt
from parallel_build.utils import better_rmtree

TEMP_DIR_PREFIX = f"ParallelBuild_{uuid.getnode()}_"


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
        if Path(path) in (
            project_path / ".git",
            project_path / "Library",
            project_path / "Logs",
            project_path / "Temp",
        ):
            return names
        return []

    return _ignore_patterns


class LocalSource(BuildStep):
    name = "Local project"

    def __init__(self, project_name: str, project_path: str, verbose: bool = False):
        self.project_name = project_name
        self.project_path = Path(project_path)
        self.interrupt = False
        self.verbose = verbose
        self.temp_dirs = []

    @BuildStep.start_method
    def __enter__(self):
        return self

    @BuildStep.end_method
    def __exit__(self, exc_type, exc_value, traceback):
        for temp_dir in self.temp_dirs:
            if Path(temp_dir).exists():
                better_rmtree(path=temp_dir)

    def interruptable_copy(self, src, dst, *, follow_symlinks=True):
        if self.interrupt:
            self.message.emit("\nProject files copy stopped")
            raise BuildProcessInterrupt
        if self.verbose:
            self.long_message.emit(f"Copying {src} to {dst}")
        return shutil.copy2(src, dst, follow_symlinks=True)

    @contextmanager
    def temporary_project(self):
        with tempfile.TemporaryDirectory(
            prefix=TEMP_DIR_PREFIX, ignore_cleanup_errors=True
        ) as temp_dir:
            self.temp_dirs.append(temp_dir)
            self.message.emit(f"Copying {self.project_name} files to {temp_dir}...")
            temp_project_path = Path(temp_dir) / self.project_name
            try:
                shutil.copytree(
                    self.project_path,
                    temp_project_path,
                    copy_function=self.interruptable_copy,
                    ignore=ignore_patterns(self.project_path),
                )
            except FileNotFoundError as e:
                raise BuildProcessError(e)
            yield temp_project_path
            self.message.emit(f"\nCleaning temporary directory {temp_dir}...")
        if Path(temp_dir).exists():
            better_rmtree(path=temp_dir)

    def stop(self):
        self.interrupt = True


class GitSource(BuildStep):
    name = "Git repository"

    def __init__(
        self, project_name: str, git_repository: str, git_polling_interval: int = 30
    ):
        self.project_name = project_name
        self.git_repository = git_repository
        self.git_polling_interval = git_polling_interval

        self.temp_dir = tempfile.TemporaryDirectory(
            prefix=TEMP_DIR_PREFIX, ignore_cleanup_errors=True
        )
        self.temp_project_path = Path(self.temp_dir.name) / project_name
        self.build_count = 0
        self.interrupt = False

    def run_git(self, git_command, *args, **kwargs):
        return self.command_executor.run(
            ["git", *git_command],
            *args,
            not_found_error_message="Cannot find `git` for repository management! Please install it: https://git-scm.com/",
            **kwargs,
        )

    @BuildStep.start_method
    def __enter__(self):
        self.temp_project_path.mkdir()
        self.short_message.emit(
            f"Cloning {self.project_name} to {self.temp_project_path}..."
        )
        self.run_git(
            ["clone", self.git_repository, self.temp_project_path],
            error_message=f"Cannot clone {self.git_repository}",
            redirect_stderr_to_stdout=True,  # git clone sends all output to stderr
        )
        return self

    @BuildStep.end_method
    def __exit__(self, exc_type, exc_value, traceback):
        self.message.emit(f"\nCleaning temporary directory {self.temp_dir.name}...")
        self.temp_dir.cleanup()
        if Path(self.temp_dir.name).exists():
            better_rmtree(path=self.temp_dir.name)

    @contextmanager
    def temporary_project(self):
        previous_commit = self.run_git(
            ["rev-parse", "HEAD"], cwd=self.temp_project_path, return_output=True
        )
        while self.build_count > 0 and not self.interrupt:
            self.run_git(["pull"], cwd=self.temp_project_path)
            current_commit = self.run_git(
                ["rev-parse", "HEAD"],
                cwd=self.temp_project_path,
                return_output=True,
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

        self.run_git(
            ["reset", "--hard", "HEAD"],
            cwd=self.temp_project_path,
        )
        self.run_git(
            ["clean", "-df"],
            cwd=self.temp_project_path,
        )
        self.build_count += 1

    def stop(self):
        self.command_executor.stop()
        self.interrupt = True


def clean_leftover_temp_dirs():
    for leftover_path in [
        file.path
        for file in os.scandir(tempfile.gettempdir())
        if file.is_dir() and file.name.startswith(TEMP_DIR_PREFIX)
    ]:
        print(f"Removing {leftover_path}")
        shutil.rmtree(leftover_path, ignore_errors=True)
