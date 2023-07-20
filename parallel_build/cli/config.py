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


@config.command()
def example():
    example_config_str = """
projects:
  - name: Black Mesa
    source:
      type: local
      value: C:\\Users\\gfreeman\\projects\\BlackMesa
    build:
      target: WebGL
      path: Builds\\WebGL
    post_build:
      - action: copy
        params:
          target: C:\\Users\\gfreeman\\projects\\BlackMesa\\Builds\\WebGL
      - action: publish-itch
        params:
          itch_user: gfreeman
          itch_game: black-mesa
          channel: webgl
  - name: Aperture Science
    source:
      type: git
      value: git@github.com:chell/aperture-science.git
    build:
      target: Windows64
      path: Builds\\Windows\\ApertureScience.exe
    post_build:
      - action: copy
        params:
          target: C:\\Users\\chell\\projects\\Git Parallel Build\\Builds\\Windows
      - action: publish-itch
        params:
          itch_user: chell
          itch_game: aperture-science
          itch_channel: win
git_polling_interval: 20
""".strip()
    print(example_config_str)
