import typer

from .set_media_item_width_height_date_taken_fields import (
    set_media_item_width_height_date_taken_fields,
)
from .dump import dump
from .restore import restore
from .delete_media_item_ids_from_albums_db import delete_media_item_ids_from_albums_db
from .delete_child_album_ids_from_albums_db import delete_child_album_ids_from_albums_db
from .delete_media_items_without_album_id import delete_media_items_without_album_id
from .initialize_map_cells_db import initialize_map_cells_db

app = typer.Typer()
app.command()(dump)
app.command()(restore)
app.command()(delete_media_item_ids_from_albums_db)
app.command()(set_media_item_width_height_date_taken_fields)
app.command()(delete_child_album_ids_from_albums_db)
app.command()(delete_media_items_without_album_id)
app.command()(initialize_map_cells_db)
