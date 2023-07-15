import click

from parallel_build.config import CONFIG_PATH


@click.group()
def config():
    ...


@config.command()
def show():
    with open(
        CONFIG_PATH,
        encoding="utf-8",
    ) as file:
        print(file.read())


@config.command()
def edit():
    click.launch(str(CONFIG_PATH), wait=True)
