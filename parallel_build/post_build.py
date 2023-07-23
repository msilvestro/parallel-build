import shutil
from pathlib import Path

from parallel_build.build_step import BuildStep
from parallel_build.config import ProjectPostBuildAction
from parallel_build.exceptions import BuildProcessError, BuildProcessInterrupt


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


class CopyBuild(BuildStep):
    name = "Copy build"

    def __init__(self, build_path: Path, target_path: str, verbose: bool = False):
        self.build_path = build_path
        self.target_path = target_path
        self.verbose = verbose

        self.interrupt = False

    def interruptable_copy(self, src, dst, *, follow_symlinks=True):
        if self.interrupt:
            self.message.emit("\nBuild files copy stopped")
            raise BuildProcessInterrupt
        if not self.verbose:
            self.long_message.emit(f"Copying {src} to {dst}")
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
        except FileNotFoundError as e:
            raise BuildProcessError(e)

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

    def run_butler(self, butler_command, *args, **kwargs):
        self.command_executor.run(
            ["butler", *butler_command],
            *args,
            not_found_error_message="Cannot find `butler` for Itch publish! Please install it: https://itch.io/docs/butler/",
            **kwargs,
        )

    @BuildStep.start_method
    @BuildStep.end_method
    def run(self):
        self.message.emit(f"Publishing to itch.io ({self.itch_path})...")
        self.run_butler(["push", str(self.build_path), self.itch_path])
        self.run_butler(["status", self.itch_path])

    @BuildStep.end_method
    def stop(self):
        self.command_executor.stop()
