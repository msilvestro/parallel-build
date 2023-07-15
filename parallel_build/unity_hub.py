from pathlib import Path

from parallel_build.utils import OperatingSystem


class UnityRecentlyUsedProjectsObserver:
    """Since Unity Hub will show the temporary project at some point after we
    start the build, we will check when it does and remove it."""

    def __init__(self, temp_project_path: Path):
        self.temp_project_path = temp_project_path
        self.key_found = False

    def check_and_remove(self):
        if self.key_found:
            return
        if OperatingSystem.current not in (
            OperatingSystem.windows,
            OperatingSystem.linux,
        ):
            return
        key_value = check_unity_recently_used_projects_paths(self.temp_project_path)
        if key_value:
            delete_unity_recently_used_projects_paths(key_value)
            self.key_found = True


def check_unity_recently_used_projects_paths(temp_project_path: Path):
    if OperatingSystem.current == OperatingSystem.windows:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, "Software\\Unity Technologies\\Unity Editor 5.x"
        ) as unity_key:
            for i in range(1024):
                try:
                    key_name, key_value, _ = winreg.EnumValue(unity_key, i)
                    if key_name.startswith("RecentlyUsedProjectPaths"):
                        project_path = Path(key_value[:-1].decode("utf-8"))
                        if project_path == temp_project_path:
                            print("FOUND!")
                            return key_name
                except WindowsError:
                    break
        return False
    elif OperatingSystem.current == OperatingSystem.macos:
        import plistlib

        with open(
            "/Users/matt/Library/Preferences/com.unity3d.UnityEditor5.x.plist", "rb"
        ) as plist:
            unity_preferences = plistlib.load(plist)
            base_key = None
            private_key = None
            for key, value in unity_preferences.items():
                if key.startswith("RecentlyUsedProjectPaths"):
                    if value == str(temp_project_path):
                        base_key = key
                    elif value == f"/private{temp_project_path}":
                        private_key = key
            return (base_key, private_key) if base_key and private_key else False
    else:
        return False


def delete_unity_recently_used_projects_paths(key_name: str):
    if OperatingSystem.current == OperatingSystem.windows:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            "Software\\Unity Technologies\\Unity Editor 5.x",
            access=winreg.KEY_WRITE,
        ) as unity_key:
            winreg.DeleteValue(unity_key, key_name)
    elif OperatingSystem.current == OperatingSystem.macos:
        import plistlib

        with open(
            "/Users/matt/Library/Preferences/com.unity3d.UnityEditor5.x.plist", "rb"
        ) as plist:
            unity_preferences = plistlib.load(plist)
        base_key, private_key = key_name
        del unity_preferences[base_key]
        del unity_preferences[private_key]
        with open(
            "/Users/matt/Library/Preferences/com.unity3d.UnityEditor5.x.plist", "wb"
        ) as plist:
            plistlib.dump(unity_preferences, plist)
