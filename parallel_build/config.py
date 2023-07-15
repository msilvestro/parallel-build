from pathlib import Path
from typing import Literal

import click
import yaml
from pydantic import BaseModel

CONFIG_PATH = Path(click.get_app_dir("ParallelBuild")) / "config.yaml"
if not CONFIG_PATH.exists():
    CONFIG_PATH.parent.mkdir(exist_ok=True)
    CONFIG_PATH.touch()


class ProjectSource(BaseModel):
    type: Literal["local", "git"]
    value: str


class ProjectBuildConfig(BaseModel):
    target: Literal[
        "Windows", "Windows64", "OSXUniversal", "Linux64", "WebGL"
    ] = "WebGL"
    path: str = "Build/WebGL"


class ProjectPostBuildAction(BaseModel):
    action: Literal["copy", "publish-itch"]
    params: dict[str, str] | None


class Projects(BaseModel):
    name: str
    source: ProjectSource
    build: ProjectBuildConfig = ProjectBuildConfig()
    post_build: list[ProjectPostBuildAction] = []


class Notification(BaseModel):
    enabled: bool = False
    theme: str = "pokemon"


class Config(BaseModel):
    projects: list[Projects]
    git_polling_interval: int = 30
    notification: Notification = Notification()

    @classmethod
    def load(cls):
        with open(
            CONFIG_PATH,
            encoding="utf-8",
        ) as file:
            config = yaml.safe_load(file.read())
        return cls.model_validate(config)

    @classmethod
    def loads(cls, config_str: str):
        config = yaml.safe_load(config_str)
        return cls.model_validate(config)
