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
        output_function=print,
        **kwargs: dict,
    ):
        source_class = {
            ProjectSourceType.local: LocalSource,
            ProjectSourceType.git: GitSource,
        }[source_type]
        self.source: LocalSource | GitSource = source_class(
            project_name, source_value, output_function, **kwargs
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.source.cleanup()
        return None

    def temporary_project(self):
        return self.source.temporary_project()

    def stop(self):
        self.source.stop()


def ignore_patterns(project_path: Path):
    def _ignore_patterns(path, names):
        if Path(path) in (project_path / "Temp", project_path / "Logs"):
            return names
        return []

    return _ignore_patterns


class Interrupt(Exception):
    """Interrupt copy operation."""


class LocalSource:
    def __init__(self, project_name: str, project_path: str, output_function, **kwargs):
        self.project_name = project_name
        self.project_path = Path(project_path)
        self.output_function = output_function
        self.interrupt = False

    def cleanup(self):
        ...

    def interruptable_copy(self, src, dst, *, follow_symlinks=True):
        if self.interrupt:
            raise Interrupt("Interrupting copy operation")
        self.output_function(f"Copying {src} to {dst}...")
        return shutil.copy2(src, dst, follow_symlinks=True)

    @contextmanager
    def temporary_project(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
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
                self.output_function("Project files copy stopped.")
                pass
            yield temp_project_path

    def stop(self):
        self.interrupt = True


class GitSource:
    def __init__(
        self, project_name: str, git_repository: str, output_function, **kwargs
    ):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.temp_project_path = Path(self.temp_dir.name) / project_name
        self.temp_project_path.mkdir()
        # strange: it seems like part of the output of git clone is sent to stderr
        run_subprocess(["git", "clone", git_repository, self.temp_project_path])
        self.build_count = 0
        self.git_polling_interval = kwargs.get("git_polling_interval", 30)
        self.output_function = output_function
        self.interrupt = False

    def cleanup(self):
        self.temp_dir.cleanup()

    @contextmanager
    def temporary_project(self):
        previous_commit = run_subprocess(
            ["git", "rev-parse", "HEAD"], cwd=self.temp_project_path
        )
        while self.build_count > 0 and not self.interrupt:
            self.output_function(
                run_subprocess(["git", "pull"], cwd=self.temp_project_path)
            )
            current_commit = run_subprocess(
                ["git", "rev-parse", "HEAD"], cwd=self.temp_project_path
            )
            if current_commit != previous_commit or self.interrupt:
                break
            self.output_function(
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
