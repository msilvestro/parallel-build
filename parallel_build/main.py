import chime
import click

from parallel_build.build import Builder
from parallel_build.config import Config
from parallel_build.post_build import execute_action
from parallel_build.source import Source
from parallel_build.unity_hub import UnityRecentlyUsedProjectsObserver


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


@click.command()
@click.option("--continuous", "-c", is_flag=True)
@click.argument("project_name")
def build(continuous: bool, project_name: str):
    config = Config.load()
    chime.theme(config.notification.theme)
    project = get_project(config, project_name)
    if project is None:
        raise Exception(f"Project '{project_name}' not found")
    with Source(
        project.name,
        project.source.type,
        project.source.value,
        git_polling_interval=config.git_polling_interval,
    ) as source:
        while True:
            with source.temporary_project() as temp_project_path:
                click.echo(
                    f"\n== Starting new build of {project.name} in {temp_project_path}..."
                )
                builder = Builder(
                    project_path=temp_project_path,
                    build_target=project.build.target,
                    build_path=project.build.path,
                )
                builder.start()
                observer = UnityRecentlyUsedProjectsObserver(temp_project_path)
                for line in builder.output_lines:
                    observer.check_and_remove()
                    print(line)
                print()
                return_value = builder.return_value
                if return_value == 0:
                    print("Success!")
                    play_notification(config, return_value)
                else:
                    print(f"Error ({return_value})")
                    print(builder.error_message)
                    play_notification(config, return_value)
                    break
                for build_action in project.post_build:
                    execute_action(build_action, builder.build_path)
            if not continuous:
                break
