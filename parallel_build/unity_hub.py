import platform
from pathlib import Path


class UnityRecentlyUsedProjectsObserver:
    """Since Unity Hub will show the temporary project at some point after we
    start the build, we will check when it does and remove it."""

    def __init__(self, temp_project_path: Path):
        self.temp_project_path = temp_project_path
        self.key_found = False

    def check_and_remove(self):
        if self.key_found:
            return
        if not platform.system() == "Windows":
            return
        key_value = check_unity_recently_used_projects_paths(self.temp_project_path)
        if key_value:
            delete_unity_recently_used_projects_paths(key_value)
            self.key_found = True


def check_unity_recently_used_projects_paths(temp_project_path: Path):
    if platform.system() == "Windows":
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
                            return key_name
                except WindowsError:
                    break
        return False
    else:
        return False


def delete_unity_recently_used_projects_paths(key_name: str):
    if platform.system() == "Windows":
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            "Software\\Unity Technologies\\Unity Editor 5.x",
            access=winreg.KEY_WRITE,
        ) as unity_key:
            winreg.DeleteValue(unity_key, key_name)
