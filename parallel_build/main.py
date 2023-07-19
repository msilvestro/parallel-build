from parallel_build.build import Builder
from parallel_build.config import Config
from parallel_build.post_build import get_post_build_action
from parallel_build.source import Source
from parallel_build.unity_hub import UnityRecentlyUsedProjectsObserver


def get_project(config: Config, project_name: str):
    for project in config.projects:
        if project.name == project_name:
            return project


def play_notification():
    print("\a")


class BuildProcess:
    def __init__(self, project_name: str, on_build_end=None):
        config = Config.load()
        project = get_project(config, project_name)
        if project is None:
            raise Exception(f"Project '{project_name}' not found")
        self.project = project
        self.git_polling_interval = config.git_polling_interval
        self.stoppable_step = None
        self.interrupt = False
        self.on_build_end = on_build_end

    def start(self, continuous: bool):
        self.interrupt = False
        with Source(
            self.project.name,
            self.project.source.type,
            self.project.source.value,
            git_polling_interval=self.git_polling_interval,
        ) as source:
            self.stoppable_step = source
            while not self.interrupt:
                with source.temporary_project() as temp_project_path:
                    if self.interrupt:
                        break
                    yield f"\n== Starting new build of {self.project.name} in {temp_project_path}..."
                    builder = Builder(
                        project_path=temp_project_path,
                        build_target=self.project.build.target,
                        build_path=self.project.build.path,
                    )
                    self.stoppable_step = builder
                    builder.start()
                    observer = UnityRecentlyUsedProjectsObserver(temp_project_path)
                    for line in builder.output_lines:
                        observer.find_and_remove()
                        yield line
                    return_value = builder.return_value
                    if return_value == 0:
                        yield "Success!"
                        play_notification()
                    else:
                        yield f"Error ({return_value})"
                        yield builder.error_message
                        play_notification()
                        break
                    for build_action in self.project.post_build:
                        if not self.interrupt:
                            post_build_action = get_post_build_action(
                                build_action, builder.build_path
                            )
                            self.stoppable_step = post_build_action
                            yield from post_build_action.run()
                if not continuous:
                    break
        if self.on_build_end:
            self.on_build_end()

    def stop(self):
        self.interrupt = True
        if self.stoppable_step:
            self.stoppable_step.stop()
