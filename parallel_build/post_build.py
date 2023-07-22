import shutil
import time
from pathlib import Path

from parallel_build.build_step import BuildStep
from parallel_build.command import Command
from parallel_build.config import ProjectPostBuildAction
from parallel_build.utils import run_subprocess


def get_post_build_action(action: ProjectPostBuildAction, build_path: str):
    build_path = Path(build_path)
    if build_path.is_file():
        build_path = build_path.parent
    if action.action == "copy":
        return CopyBuild(build_path, action.params["target"])
    elif action.action == "publish-itch":
        return PublishItch(
            build_path,
            action.params["itch_user"],
            action.params["itch_game"],
            action.params["itch_channel"],
        )


class Interrupt(Exception):
    """Interrupt copy operation."""


class CopyBuild(BuildStep):
    name = "Copy build"

    def __init__(self, build_path: Path, target_path: str, verbose: bool = False):
        self.build_path = build_path
        self.target_path = target_path
        self.verbose = verbose

        self.interrupt = False

    def interruptable_copy(self, src, dst, *, follow_symlinks=True):
        if self.interrupt:
            raise Interrupt("Interrupting copy operation")
        if not self.verbose:
            self.long_message.emit(f"Copying {src} to {dst}")
        time.sleep(1)
        return shutil.copy2(src, dst, follow_symlinks=True)

    @BuildStep.start_method
    @BuildStep.end_method
    def run(self):
        target_path = Path(self.target_path)
        target_path.mkdir(exist_ok=True, parents=True)
        self.message.emit(f"Copy build from {self.build_path} to {target_path}")
        try:
            shutil.copytree(
                self.build_path,
                target_path,
                dirs_exist_ok=True,
                copy_function=self.interruptable_copy,
            )
        except Interrupt:
            self.message.emit("Project files copy stopped")

    @BuildStep.end_method
    def stop(self):
        self.interrupt = True


class PublishItch(BuildStep):
    name = "Publish on itch.io"

    def __init__(
        self, build_path: Path, itch_user: str, itch_game: str, itch_channel: str
    ):
        self.build_path = build_path
        self.itch_path = f"{itch_user}/{itch_game}:{itch_channel}"
        self.push_process = None

    @BuildStep.start_method
    @BuildStep.end_method
    def run(self):
        self.message.emit(f"Publishing to itch.io ({self.itch_path})...")
        try:
            self.push_process = Command(
                " ".join(["butler", "push", str(self.build_path), self.itch_path])
            )
            self.push_process.start()
            for line in self.push_process.output_lines:
                self.long_message.emit(line)
            self.long_message.emit(run_subprocess(["butler", "status", self.itch_path]))
        except FileNotFoundError:
            self.error.emit(
                "Cannot find `butler` for Itch publish! Please install it: https://itch.io/docs/butler/"
            )

    @BuildStep.end_method
    def stop(self):
        if self.push_process:
            self.push_process.stop()
