import typer

from sharded_photos_drive_cli_client.cli2.commands.config import add
from sharded_photos_drive_cli_client.cli2.commands.config import reauthorize
from sharded_photos_drive_cli_client.cli2.commands.config.init import init


app = typer.Typer()
app.command()(init)
app.add_typer(add.app, name="add")
app.add_typer(reauthorize.app, name="reauthorize")
