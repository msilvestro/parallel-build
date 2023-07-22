import subprocess

import click


@click.command()
def check():
    for command, reason, install_link in [
        ("git", "source of git type", "https://git-scm.com/"),
        ("butler", "Itch publish", "https://itch.io/docs/butler/"),
    ]:
        try:
            output = (
                subprocess.check_output([command, "--version"]).decode("utf-8").strip()
            )
            click.secho(f"[✓] {command}: {output}", fg="green")
        except FileNotFoundError:
            click.secho(
                f"[✘] Cannot find '{command}' for {reason}! Please install it: {install_link}",
                fg="red",
            )
