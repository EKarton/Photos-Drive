import typer

from .set_media_item_width_height_date_taken_fields import (
    set_media_item_width_height_date_taken_fields,
)
from .delete_media_item_ids import delete_media_item_ids
from .dump import dump
from .restore import restore


app = typer.Typer()
app.command()(dump)
app.command()(restore)
app.command()(delete_media_item_ids)
app.command()(set_media_item_width_height_date_taken_fields)
