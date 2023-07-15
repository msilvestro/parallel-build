import click

from parallel_build.build_cli import build
from parallel_build.check_cli import check
from parallel_build.config_cli import config
from parallel_build.gui.cli import gui


@click.group()
def cli():
    ...


cli.add_command(build)
cli.add_command(check)
cli.add_command(config)
cli.add_command(gui)

if __name__ == "__main__":
    cli()
