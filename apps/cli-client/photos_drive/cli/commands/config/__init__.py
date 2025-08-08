import typer

from photos_drive.cli.commands.config import add, reauthorize
from photos_drive.cli.commands.config.init import init
from photos_drive.cli.commands.config.view import view

app = typer.Typer()
app.command()(view)
app.command()(init)
app.add_typer(add.app, name="add")
app.add_typer(reauthorize.app, name="reauthorize")
