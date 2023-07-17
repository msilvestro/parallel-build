from parallel_build.build import Builder
from parallel_build.config import Config
from parallel_build.post_build import execute_action
from parallel_build.source import Source
from parallel_build.unity_hub import UnityRecentlyUsedProjectsObserver


def get_project(config: Config, project_name: str):
    for project in config.projects:
        if project.name == project_name:
            return project


def play_notification():
    print("\a")


def build(continuous: bool, project_name: str):
    config = Config.load()
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
                yield f"\n== Starting new build of {project.name} in {temp_project_path}..."
                builder = Builder(
                    project_path=temp_project_path,
                    build_target=project.build.target,
                    build_path=project.build.path,
                )
                builder.start()
                observer = UnityRecentlyUsedProjectsObserver(temp_project_path)
                for line in builder.output_lines:
                    observer.find_and_remove()
                    yield line
                yield ""
                return_value = builder.return_value
                if return_value == 0:
                    yield "Success!"
                    play_notification()
                else:
                    yield f"Error ({return_value})"
                    yield builder.error_message
                    play_notification()
                    break
                for build_action in project.post_build:
                    yield from execute_action(build_action, builder.build_path)
            if not continuous:
                break
