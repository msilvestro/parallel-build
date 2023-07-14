import io
import platform
import subprocess
from pathlib import Path

import yaml

MAX_LINES = 3108


def get_build_path(project_path: str, build_path: str):
    build_path = Path(build_path)
    if not build_path.is_absolute():
        return project_path / build_path
    return build_path


def get_editor_path(editor_version: str):
    if platform.system() == "Windows":
        return f'"C:\\Program Files\\Unity\\Hub\\Editor\\{editor_version}\\Editor\\Unity.exe"'
    elif platform.system() == "Darwin":
        return f"/Applications/Unity/Hub/Editor/{editor_version}/Unity.app/Contents/MacOS/Unity"
    elif platform.system() == "Linux":
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
        with open(editor_path / "WebGLBuilder.cs", "a") as f:
            f.write(WEBGL_BUILDER)
        return (
            f"-executeMethod ParallelBuild.WebGLBuilder.Build -buildpath {build_path}"
        )
    return f'-build{build_target}Player "{build_path}"'


class Builder:
    def __init__(self, project_path, build_target, build_path):
        project_path = Path(project_path)
        self.build_path = get_build_path(project_path, build_path)

        with open(
            project_path / "ProjectSettings" / "ProjectVersion.txt", encoding="utf-8"
        ) as f:
            project_version_yaml = yaml.safe_load(f.read())
        editor_version = project_version_yaml["m_EditorVersion"]

        self.command = " ".join(
            [
                get_editor_path(editor_version),
                "-quit",
                "-batchmode",
                f'-projectpath "{project_path}"',
                "-logFile -",
                get_build_args(project_path, build_target, build_path),
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
