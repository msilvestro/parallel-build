import sys
from parallel_build.build import Builder
from parallel_build.config import Config
from parallel_build.source import Source
import chime


def get_project(config: Config, project_name: str):
    for project in config.projects:
        if project.name == project_name:
            return project


def play_notification(config: Config, return_value: int):
    if not config.notification.enabled:
        return
    if return_value == 0:
        chime.success()
    else:
        chime.error()


if __name__ == "__main__":
    config = Config.load()
    chime.theme(config.notification.theme)
    project_name = sys.argv[1]
    project = get_project(config, project_name)
    if project is None:
        raise Exception(f"Project '{project_name}' not found")
    source = Source(project.source.type, project.source.value)
    with source.temporary_project() as temp_project_path:
        builder = Builder(
            project_path=temp_project_path,
            build_path=project.build.path,
            build_method=project.build.method,
        )
        play_notification(config, 0)
        # builder.start()
        # for percentage, line in builder.output_lines:
        #     print(f"{percentage:0.2f}% | {line}")
        # print()
        # return_value = builder.return_value
        # if return_value == 0:
        #     print(f"Success!")
        # else:
        #     print(f"Error ({return_value})")
        #     print(builder.error_message)
        # play_notification(config, return_value)
