from enum import Enum
from pathlib import Path
from typing import Literal

import msgspec
from msgspec import Struct

from parallel_build.utils import get_app_dir

CONFIG_PATH = Path(get_app_dir("ParallelBuild")) / "config.yaml"


class Base(Struct, kw_only=True):
    ...


class ProjectSourceType(str, Enum):
    local = "local"
    git = "git"


class ProjectSource(Base):
    type: ProjectSourceType
    value: str


class BuildTarget(str, Enum):
    windows = "Windows"
    windows64 = "Windows 64"
    macos = "OSXUniversal"
    linux = "Linux64"
    webgl = "WebGL"


class ProjectBuildConfig(Base):
    target: BuildTarget = BuildTarget.webgl
    path: str = "Build/WebGL"


class ProjectPostBuildAction(Base):
    action: Literal["copy", "publish-itch"]
    params: dict[str, str] | None


class Project(Base):
    name: str
    source: ProjectSource
    build: ProjectBuildConfig
    post_build: list[ProjectPostBuildAction] = []


class Config(Base):
    projects: list[Project] = []
    git_polling_interval: int = 30

    @classmethod
    def load(cls):
        if not CONFIG_PATH.exists():
            CONFIG_PATH.parent.mkdir(exist_ok=True)
            CONFIG_PATH.touch()
        with open(
            CONFIG_PATH,
            "rb",
        ) as file:
            config = file.read()
            if not config:
                return cls()
            return msgspec.yaml.decode(config, type=cls)

    @classmethod
    def loads(cls, config_str: str):
        return msgspec.yaml.decode(config_str)

    def save(self):
        with open(
            CONFIG_PATH,
            "wb",
        ) as file:
            yaml_config = msgspec.yaml.encode(self)
            file.write(yaml_config)
