import click

from parallel_build.build_step import BuildStep
from parallel_build.main import BuildProcess


def start_echo(name: str):
    click.secho(f"\n> {name}", fg="green")


def end_echo(name: str):
    click.secho("> End", fg="green")


def error_echo(error: str):
    click.secho(error, fg="red")


@click.command()
@click.argument("project_name")
@click.option("--continuous", "-c", is_flag=True)
def build(project_name: str, continuous: bool):
    BuildStep.start.set(start_echo)
    BuildStep.message.set(click.echo)
    BuildStep.error.set(error_echo)
    BuildStep.end.set(end_echo)

    click.secho("// Parallel Build", fg="green")

    build_process = BuildProcess(
        project_name=project_name,
    )
    try:
        build_process.run(continuous)
    except KeyboardInterrupt:
        build_process.stop()
