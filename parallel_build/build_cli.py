import click

from parallel_build.logger import Logger
from parallel_build.main import BuildProcess


@click.command()
@click.argument("project_name")
@click.option("--continuous", "-c", is_flag=True)
def build(project_name: str, continuous: bool):
    Logger.output_function = click.echo
    build_process = BuildProcess(
        project_name=project_name,
    )
    try:
        for output in build_process.start(continuous):
            click.echo(output)
    except KeyboardInterrupt:
        build_process.stop()
