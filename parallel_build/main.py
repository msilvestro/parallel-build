from typing import Callable

from parallel_build.build_step import BuildStep
from parallel_build.config import Config
from parallel_build.exceptions import BuildProcessError, BuildProcessInterrupt
from parallel_build.post_build import get_post_build_action
from parallel_build.source import get_source
from parallel_build.unity_builder import UnityBuilder
from parallel_build.unity_hub import UnityRecentlyUsedProjectsObserver


def get_project(config: Config, project_name: str):
    for project in config.projects:
        if project.name == project_name:
            return project


class BuildProcess:
    def __init__(
        self, project_name: str, on_build_end: Callable[[bool], None] | None = None
    ):
        config = Config.load()
        project = get_project(config, project_name)
        if project is None:
            raise Exception(f"Project '{project_name}' not found")
        self.project = project
        self.git_polling_interval = config.git_polling_interval
        self.current_build_step = None
        self.interrupt = False
        self.on_build_end = on_build_end

    def run(self, continuous: bool):
        self.interrupt = False
        finished_with_success = True
        try:
            with get_source(
                self.project.name,
                self.project.source.type,
                self.project.source.value,
                git_polling_interval=self.git_polling_interval,
            ) as source:
                self.current_build_step = source
                while not self.interrupt:
                    with source.temporary_project() as temp_project_path:
                        if self.interrupt:
                            break

                        builder = UnityBuilder(
                            project_name=self.project.name,
                            project_path=temp_project_path,
                            build_target=self.project.build.target,
                            build_method=self.project.build.method,
                            build_path=self.project.build.path,
                        )
                        self.current_build_step = builder
                        observer = UnityRecentlyUsedProjectsObserver(temp_project_path)
                        builder.progress.set(observer.find_and_remove)
                        return_value = builder.run()
                        if return_value != 0:
                            print("\a")
                            finished_with_success = False
                            break

                        for build_action in self.project.post_build:
                            if self.interrupt:
                                break
                            post_build_action = get_post_build_action(
                                build_action, builder.build_path
                            )
                            self.current_build_step = post_build_action
                            post_build_action.run()

                        print("\a")
                    if not continuous:
                        break
        except BuildProcessError as e:
            finished_with_success = False
            BuildStep.error.emit(str(e))
        except BuildProcessInterrupt as e:
            finished_with_success = False
            BuildStep.message.emit(str(e))
        if self.on_build_end:
            self.on_build_end(finished_with_success)

    def stop(self):
        self.interrupt = True
        if self.current_build_step:
            self.current_build_step.stop()
