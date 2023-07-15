from pathlib import Path

from parallel_build.utils import OperatingSystem

if OperatingSystem.current == OperatingSystem.windows:
    import winreg
elif OperatingSystem.current == OperatingSystem.macos:
    import plistlib


class WindowsUnityRecentlyUsedProjects:
    REGISTRY_PATH = "Software\\Unity Technologies\\Unity Editor 5.x"

    def __init__(self):
        if OperatingSystem.current != OperatingSystem.windows:
            raise Exception("This class works only on Windows")

    def check(self, project_path: Path):
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.REGISTRY_PATH) as unity_key:
            for i in range(1024):
                try:
                    value_name, value_data, _ = winreg.EnumValue(unity_key, i)
                    if value_name.startswith("RecentlyUsedProjectPaths"):
                        project_path = Path(value_data[:-1].decode("utf-8"))
                        if project_path == project_path:
                            return value_name
                except WindowsError:
                    break
        return False

    def delete(self, value_name: str):
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            self.REGISTRY_PATH,
            access=winreg.KEY_WRITE,
        ) as unity_key:
            winreg.DeleteValue(unity_key, value_name)


class MacOSUnityRecentlyUsedProjects:
    PLIST_PATH = "/Users/matt/Library/Preferences/com.unity3d.UnityEditor5.x.plist"

    def __init__(self):
        if OperatingSystem.current != OperatingSystem.macos:
            raise Exception("This class works only on MacOS")

    def check(self, project_path: Path):
        with open(self.PLIST_PATH, "rb") as plist_file:
            unity_plist = plistlib.load(plist_file)
            base_key = None
            private_key = None
            for key, value in unity_plist.items():
                if key.startswith("RecentlyUsedProjectPaths"):
                    if value == str(project_path):
                        base_key = key
                    elif value == f"/private{project_path}":
                        private_key = key
            return (base_key, private_key) if base_key and private_key else False

    def delete(self, keys: tuple[str, str]):
        with open(self.PLIST_PATH, "rb") as plist_file:
            unity_plist = plistlib.load(plist_file)
        base_key, private_key = keys
        del unity_plist[base_key]
        del unity_plist[private_key]
        with open(self.PLIST_PATH, "wb") as plist_file:
            plistlib.dump(unity_plist, plist_file)


class UnityRecentlyUsedProjectsObserver:
    """Since Unity Hub will show the temporary project at some point after we
    start the build, we will check when it does and remove it."""

    def __init__(self, temp_project_path: Path):
        self.handler = self._get_handler()
        self.temp_project_path = temp_project_path
        self.key_found = False

    def _get_handler(self):
        match OperatingSystem.current:
            case OperatingSystem.windows:
                return WindowsUnityRecentlyUsedProjects()
            case OperatingSystem.macos:
                return MacOSUnityRecentlyUsedProjects()
            case _:
                return None

    def check_and_remove(self):
        if not self.handler:
            return
        if self.key_found:
            return
        key = self.handler.check(self.temp_project_path)
        if key:
            self.handler.delete(key)
            self.key_found = True
