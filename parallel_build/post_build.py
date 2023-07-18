import shutil
import time
from pathlib import Path

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


class CopyBuild:
    def __init__(self, build_path: Path, target_path: str):
        self.build_path = build_path
        self.target_path = target_path

        self.interrupt = False

    def interruptable_copy(self, src, dst, *, follow_symlinks=True):
        if self.interrupt:
            raise Interrupt("Interrupting copy operation")
        print(f"Copy {src} to {dst}")
        time.sleep(1)
        return shutil.copy2(src, dst, follow_symlinks=True)

    def run(self):
        target_path = Path(self.target_path)
        if self.interrupt:
            return
        target_path.mkdir(exist_ok=True, parents=True)
        if self.interrupt:
            return
        yield f"\n== Post build: copy build from {self.build_path} to {target_path}"
        try:
            shutil.copytree(
                self.build_path,
                target_path,
                dirs_exist_ok=True,
                copy_function=self.interruptable_copy,
            )
        except Interrupt:
            yield "Project files copy stopped."

    def stop(self):
        self.interrupt = True


class PublishItch:
    def __init__(
        self, build_path: Path, itch_user: str, itch_game: str, itch_channel: str
    ):
        self.build_path = build_path
        self.itch_path = f"{itch_user}/{itch_game}:{itch_channel}"
        self.push_process = None

    def run(self):
        yield f"\n== Post buid: publishing to itch ({self.itch_path})..."
        try:
            self.push_process = Command(
                " ".join(["butler", "push", str(self.build_path), self.itch_path])
            )
            self.push_process.start()
            yield from self.push_process.output_lines
            yield run_subprocess(["butler", "status", self.itch_path])
        except FileNotFoundError:
            yield "Cannot find `butler` for Itch publish! Please install it: https://itch.io/docs/butler/"

    def stop(self):
        if self.push_process:
            self.push_process.stop()
