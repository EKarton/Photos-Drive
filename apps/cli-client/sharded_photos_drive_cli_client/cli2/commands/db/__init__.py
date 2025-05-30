import typer

from .dump import dump
from .restore import restore


app = typer.Typer()
app.command()(dump)
app.command()(restore)
