import typer

from . import add
from . import reauthorize
from .view import view
from .init import init


app = typer.Typer()
app.command()(view)
app.command()(init)
app.add_typer(add.app, name="add")
app.add_typer(reauthorize.app, name="reauthorize")
