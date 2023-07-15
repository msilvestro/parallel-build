import shutil
from pathlib import Path

from parallel_build.config import ProjectPostBuildAction
from parallel_build.utils import run_subprocess


def execute_action(action: ProjectPostBuildAction, build_path: str):
    build_path = Path(build_path)
    if build_path.is_file():
        build_path = build_path.parent
    if action.action == "copy":
        yield from copy_build(build_path, action.params["target"])
    elif action.action == "publish-itch":
        yield from publish_itch(
            build_path,
            action.params["itch_user"],
            action.params["itch_game"],
            action.params["itch_channel"],
        )


def copy_build(build_path: Path, target_path: str):
    target_path = Path(target_path)
    target_path.mkdir(exist_ok=True, parents=True)
    yield f"\n== Post build: copy build from {build_path} to {target_path}"
    shutil.copytree(build_path, target_path, dirs_exist_ok=True)


def publish_itch(build_path: Path, itch_user: str, itch_game: str, itch_channel: str):
    itch_path = f"{itch_user}/{itch_game}:{itch_channel}"
    yield f"\n== Post buid: publishing to itch ({itch_path})..."
    try:
        yield run_subprocess(["butler", "push", build_path, itch_path])
        yield run_subprocess(["butler", "status", itch_path])
    except FileNotFoundError:
        yield "Cannot find `butler` for Itch publish! Please install it: https://itch.io/docs/butler/"
