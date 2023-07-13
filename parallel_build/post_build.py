import shutil
import subprocess

from parallel_build.config import ProjectPostBuildAction


def execute_action(action: ProjectPostBuildAction, build_path: str):
    if action.action == "copy":
        copy_build(build_path, action.params["target"])
    elif action.action == "publish-itch":
        publish_itch(build_path, action.params["itch_user"], action.params["itch_game"])


def copy_build(build_path: str, target_path: str):
    print(f"\n== Post build: copy build from {build_path} to {target_path}")
    shutil.copytree(build_path, target_path, dirs_exist_ok=True)


def publish_itch(build_path: str, itch_user: str, itch_game: str):
    itch_path = f"{itch_user}/{itch_game}:webgl"
    print(f"\n== Post buid: publishing to itch ({itch_path})...")
    subprocess.run(["butler", "push", build_path, itch_path])
    subprocess.run(["butler", "status", itch_path])
