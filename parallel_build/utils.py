import os
import platform
import shutil
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


def get_app_dir(app_name: str) -> str:
    """Returns the config folder for the application.

    Adapted from `click.get_app_dir` to be able to avoid click dependencies for the GUI.
    """
    if OperatingSystem.current == OperatingSystem.windows:
        folder = os.environ.get("APPDATA")
        if folder is None:
            folder = os.path.expanduser("~")
        return os.path.join(folder, app_name)
    elif OperatingSystem.current == OperatingSystem.macos:
        return os.path.join(
            os.path.expanduser("~/Library/Application Support"), app_name
        )


def better_rmtree(path):
    """This `rmtree` can also handle paths that are too long in Windows.

    See https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation?tabs=registry
    """
    if OperatingSystem.current != OperatingSystem.windows:
        shutil.rmtree(path=path, ignore_errors=True)
        return

    def onerror(func, path, exc_info):
        if issubclass(exc_info[0], FileNotFoundError):
            try:
                func("\\\\?\\" + path)
            except Exception:
                print(f"Couldn't delete {path}")
                pass

    shutil.rmtree(path=path, onerror=onerror)
