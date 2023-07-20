import platform
import subprocess
from enum import Enum


class OperatingSystem(Enum):
    windows = "Windows"
    macos = "MacOS"
    unkwnow = "Unknown"

    @classmethod
    @property
    def current(cls):
        match platform.system():
            case "Windows":
                return cls.windows
            case "Darwin":
                return cls.macos
            case _:
                return cls.unkwnow

    @classmethod
    @property
    def monospace_font(cls):
        match cls.current:
            case cls.windows:
                return "Lucida Console"
            case cls.macos:
                return "Monaco"
            case _:
                return "Monaco"


def run_subprocess(*args, **kwargs) -> str:
    return subprocess.check_output(*args, **kwargs).decode("utf-8").strip()
