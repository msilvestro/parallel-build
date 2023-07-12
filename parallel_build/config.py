from typing import Literal
import platformdirs
from pydantic import BaseModel
import yaml


class ProjectSource(BaseModel):
    type: Literal["local", "git"]
    value: str


class ProjectBuildConfig(BaseModel):
    path: str = "Build/WebGL"
    method: str = "ParallelBuild.WebGLBuilder.Build"


class Projects(BaseModel):
    name: str
    source: ProjectSource
    build: ProjectBuildConfig


class Notification(BaseModel):
    enabled: bool = False
    theme: str = "pokemon"


class Config(BaseModel):
    projects: list[Projects]
    notification: Notification

    @classmethod
    def load(cls):
        with open(
            platformdirs.user_data_path() / "ParallelBuild" / "config.yaml",
            encoding="utf-8",
        ) as f:
            config = yaml.safe_load(f.read())
        return cls.model_validate(config)
