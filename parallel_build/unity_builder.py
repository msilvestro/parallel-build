import platform
from pathlib import Path

import yaml

from parallel_build.build_step import BuildStep, BuildStepEvent
from parallel_build.command import Command
from parallel_build.config import BuildTarget
from parallel_build.utils import OperatingSystem

MAX_LINES = 3108


def get_build_path(project_path: Path, build_path: str):
    build_path = Path(build_path)
    if not build_path.is_absolute():
        return project_path / build_path
    return build_path


def get_editor_path(editor_version: str):
    if OperatingSystem.current == OperatingSystem.windows:
        return f'"C:\\Program Files\\Unity\\Hub\\Editor\\{editor_version}\\Editor\\Unity.exe"'
    elif OperatingSystem.current == OperatingSystem.macos:
        return f"/Applications/Unity/Hub/Editor/{editor_version}/Unity.app/Contents/MacOS/Unity"
    elif OperatingSystem.current == OperatingSystem.linux:
        return f"/Applications/Unity/Hub/Editor/{editor_version}/Unity.app/Contents/Linux/Unity"
    else:
        raise Exception(f"Platform {platform.system()} not supported")


WEBGL_BUILDER = """
using System;
using System.Linq;
using UnityEditor;

namespace ParallelBuild
{
    public class WebGLBuilder
    {
        private static string[] GetAllScenes()
        {
            return EditorBuildSettings.scenes
                 .Where(scene => scene.enabled)
                 .Select(scene => scene.path)
                 .ToArray();
        }

        private static string GetArg(string name, string defaultValue = null)
        {
            var args = Environment.GetCommandLineArgs();
            for (int i = 0; i < args.Length; i++)
            {
                if (args[i] == name && args.Length > i + 1)
                {
                    return args[i + 1];
                }
            }
            return defaultValue;
        }

        public static bool Build()
        {
            return Build(GetArg("-buildpath", "Build/WebGL"));
        }

        public static bool Build(string buildPath)
        {
            BuildPlayerOptions options = new BuildPlayerOptions()
            {
                locationPathName = buildPath,
                target = BuildTarget.WebGL,
                scenes = GetAllScenes()
            };
            var buildReport = BuildPipeline.BuildPlayer(options);
            return buildReport.summary.result == UnityEditor.Build.Reporting.BuildResult.Succeeded;
        }
    }
}
"""


def get_build_args(project_path: Path, build_target, build_path):
    if build_target == "WebGL":
        editor_path = project_path / "Assets" / "Editor"
        editor_path.mkdir(exist_ok=True, parents=True)
        with open(editor_path / "WebGLBuilder.cs", "w") as f:
            f.write(WEBGL_BUILDER)
        return (
            f"-executeMethod ParallelBuild.WebGLBuilder.Build -buildpath {build_path}"
        )
    return f'-build{build_target}Player "{build_path}"'


class UnityBuilder(BuildStep):
    progress = BuildStepEvent()

    name = "Unity builder"

    def __init__(
        self,
        project_name: str,
        project_path: Path,
        build_target: BuildTarget,
        build_path: str,
    ):
        self.project_name = project_name
        self.project_path = Path(project_path)
        self.build_path = get_build_path(project_path, build_path)

        with open(
            self.project_path / "ProjectSettings" / "ProjectVersion.txt",
            encoding="utf-8",
        ) as f:
            project_version_yaml = yaml.safe_load(f.read())
        editor_version = project_version_yaml["m_EditorVersion"]

        self.build_command = Command(
            " ".join(
                [
                    get_editor_path(editor_version),
                    "-quit",
                    "-batchmode",
                    f'-projectpath "{self.project_path}"',
                    "-logFile -",
                    get_build_args(self.project_path, build_target, build_path),
                ]
            )
        )

    @BuildStep.start_method
    @BuildStep.end_method
    def run(self):
        self.message.emit(
            f"Starting new build of {self.project_name} in {self.project_path}..."
        )
        self.build_command.start()
        error_message = ""

        inside_error_message = False
        for line in self.build_command.output_lines:
            line = line.strip()
            if inside_error_message:
                if line == "":
                    inside_error_message = False
                else:
                    error_message += line + "\n"
            if line == "Aborting batchmode due to failure:":
                inside_error_message = True
            self.message.emit(line)
            self.progress.emit()

        return_value = self.build_command.return_value
        if return_value == 0:
            self.message.emit("Success!")
        else:
            self.error.emit(f"Error ({return_value})")
            self.error.emit(error_message)

        return return_value

    @BuildStep.end_method
    def stop(self):
        self.build_command.stop()
        self.message.emit("\nUnity build stopped")
