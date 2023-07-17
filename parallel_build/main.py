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


builder: Builder = None


class BuildProcess:
    def __init__(self, project_name: str, on_build_end=None):
        config = Config.load()
        project = get_project(config, project_name)
        if project is None:
            raise Exception(f"Project '{project_name}' not found")
        self.project = project
        self.git_polling_interval = config.git_polling_interval
        self.builder: Builder = None
        self.should_stop = False
        self.on_build_end = on_build_end

    def start(self, continuous: bool):
        self.should_stop = False
        with Source(
            self.project.name,
            self.project.source.type,
            self.project.source.value,
            git_polling_interval=self.git_polling_interval,
        ) as source:
            while not self.should_stop:
                with source.temporary_project() as temp_project_path:
                    if self.should_stop:
                        break
                    yield f"\n== Starting new build of {self.project.name} in {temp_project_path}..."
                    self.builder = Builder(
                        project_path=temp_project_path,
                        build_target=self.project.build.target,
                        build_path=self.project.build.path,
                    )
                    self.builder.start()
                    observer = UnityRecentlyUsedProjectsObserver(temp_project_path)
                    for line in self.builder.output_lines:
                        observer.find_and_remove()
                        yield line
                    yield ""
                    return_value = self.builder.return_value
                    if return_value == 0:
                        yield "Success!"
                        play_notification()
                    else:
                        yield f"Error ({return_value})"
                        yield self.builder.error_message
                        play_notification()
                        break
                    for build_action in self.project.post_build:
                        yield from execute_action(build_action, self.builder.build_path)
                if not continuous:
                    break
        if self.on_build_end:
            self.on_build_end()

    def stop(self):
        self.should_stop = True
        if self.builder:
            self.builder.stop()
