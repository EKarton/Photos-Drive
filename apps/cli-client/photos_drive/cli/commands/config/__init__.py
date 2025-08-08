import typer

from . import add, reauthorize
from .init import init
from .view import view

app = typer.Typer()
app.command()(view)
app.command()(init)
app.add_typer(add.app, name="add")
app.add_typer(reauthorize.app, name="reauthorize")
