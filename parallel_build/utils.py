import platform
from enum import Enum


class OperatingSystem(Enum):
    windows = "Windows"
    macos = "MacOS"
    linux = "Linux"
    unkwnow = "Unknown"

    @classmethod
    @property
    def current(cls):
        match platform.system():
            case "Windows":
                return cls.windows
            case "Darwin":
                return cls.macos
            case "Linux":
                return cls.linux
            case _:
                return cls.unkwnow