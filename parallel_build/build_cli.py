import click

from parallel_build.main import build as run_build


@click.command()
@click.option("--continuous", "-c", is_flag=True)
@click.argument("project_name")
def build(continuous: bool, project_name: str):
    for output in run_build(continuous, project_name):
        click.echo(output)
