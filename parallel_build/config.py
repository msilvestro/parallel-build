from typing import Literal

import platformdirs
import yaml
from pydantic import BaseModel


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
            platformdirs.user_data_path() / "ParallelBuild" / "config.yaml",
            encoding="utf-8",
        ) as f:
            config = yaml.safe_load(f.read())
        return cls.model_validate(config)
