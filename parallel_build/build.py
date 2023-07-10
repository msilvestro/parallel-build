import io
from pathlib import Path
import sys
import yaml
import subprocess

MAX_LINES = 3108


class WebGLBuilder:
    def __init__(self, project_path, build_path=None):
        project_path = Path(project_path)
        if not build_path:
            build_path = project_path / "Build" / "WebGL"

        with open(
            project_path / "ProjectSettings" / "ProjectVersion.txt", encoding="utf-8"
        ) as f:
            project_version_yaml = yaml.safe_load(f.read())
        editor_version = project_version_yaml["m_EditorVersion"]

        command = " ".join(
            [
                f'"C:\\Program Files\\Unity\\Hub\\Editor\\{editor_version}\\Editor\\Unity.exe"',
                "-quit",
                "-batchmode",
                f'-projectpath "{project_path}"',
                "-logFile -",
                "-executeMethod ParallelBuild.WebGLBuilder.Build",
                f'-buildpath "{build_path}"',
            ]
        )
        self.build_process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        self.error_message = ""

    @property
    def output_lines(self):
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


if __name__ == "__main__":
    builder = WebGLBuilder(project_path=sys.argv[1])
    for percentage, line in builder.output_lines:
        print(f"{percentage:0.2f}% | {line}")
    print()
    return_value = builder.return_value
    if return_value == 0:
        print(f"Success!")
    else:
        print(f"Error ({return_value})")
        print(builder.error_message)
