import click

from parallel_build.cli.build import build
from parallel_build.cli.check import check
from parallel_build.cli.config import config


@click.group()
def cli():
    ...


cli.add_command(build)
cli.add_command(check)
cli.add_command(config)

if __name__ == "__main__":
    cli()
