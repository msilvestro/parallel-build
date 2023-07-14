import shutil
import subprocess
from pathlib import Path

from parallel_build.config import ProjectPostBuildAction


def execute_action(action: ProjectPostBuildAction, build_path: str):
    build_path = Path(build_path)
    if build_path.is_file():
        build_path = build_path.parent
    if action.action == "copy":
        copy_build(build_path, action.params["target"])
    elif action.action == "publish-itch":
        publish_itch(
            build_path,
            action.params["itch_user"],
            action.params["itch_game"],
            action.params["itch_channel"],
        )


def copy_build(build_path: Path, target_path: str):
    target_path = Path(target_path)
    target_path.mkdir(exist_ok=True, parents=True)
    print(f"\n== Post build: copy build from {build_path} to {target_path}")
    shutil.copytree(build_path, target_path, dirs_exist_ok=True)


def publish_itch(build_path: Path, itch_user: str, itch_game: str, itch_channel: str):
    itch_path = f"{itch_user}/{itch_game}:{itch_channel}"
    print(f"\n== Post buid: publishing to itch ({itch_path})...")
    try:
        subprocess.run(["butler", "push", build_path, itch_path])
        subprocess.run(["butler", "status", itch_path])
    except FileNotFoundError:
        print(
            "Cannot find `butler` for Itch publish! Please install it: https://itch.io/docs/butler/"
        )
