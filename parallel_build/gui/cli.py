import click

from parallel_build.gui.gui import show_gui


@click.command()
def gui():
    show_gui()
