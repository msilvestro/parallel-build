import io
import subprocess
from pathlib import Path

import yaml

MAX_LINES = 3108


def get_build_path(project_path: str, build_path: str):
    build_path = Path(build_path)
    if not build_path.is_absolute():
        return project_path / build_path
    return build_path


class Builder:
    def __init__(self, project_path, build_path, build_method):
        project_path = Path(project_path)
        self.build_path = get_build_path(project_path, build_path)

        with open(
            project_path / "ProjectSettings" / "ProjectVersion.txt", encoding="utf-8"
        ) as f:
            project_version_yaml = yaml.safe_load(f.read())
        editor_version = project_version_yaml["m_EditorVersion"]

        self.command = " ".join(
            [
                f'"C:\\Program Files\\Unity\\Hub\\Editor\\{editor_version}\\Editor\\Unity.exe"',
                "-quit",
                "-batchmode",
                f'-projectpath "{project_path}"',
                "-logFile -",
                f"-executeMethod {build_method}",
                f'-buildpath "{self.build_path}"',
            ]
        )
        self.build_process = None
        self.error_message = ""

    def start(self):
        self.build_process = subprocess.Popen(
            self.command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        self.error_message = ""

    @property
    def output_lines(self):
        if not self.build_process:
            raise Exception("Build command not started")
        i = -1
        inside_error_message = False
        for line in io.TextIOWrapper(self.build_process.stdout, encoding="utf-8"):
            i += 1
            line = line.strip()
            if inside_error_message:
                if line == "":
                    inside_error_message = False
                else:
                    self.error_message += line + "\n"
            if line == "Aborting batchmode due to failure:":
                inside_error_message = True
            estimated_percentage = min(i / MAX_LINES * 100, 100)
            yield estimated_percentage, line

    @property
    def return_value(self):
        return self.build_process.wait()
