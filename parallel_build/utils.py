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
        if platform.system() == "Windows":
            return cls.windows
        elif platform.system() == "Darwin":
            return cls.macos
        elif platform.system() == "Linux":
            return cls.linux
        else:
            return cls.unkwnow
