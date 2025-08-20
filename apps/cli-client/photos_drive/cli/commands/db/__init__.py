import typer

from photos_drive.cli.commands.db.delete_child_album_ids_from_albums_db import (
    delete_child_album_ids_from_albums_db,
)
from photos_drive.cli.commands.db.delete_media_item_ids_from_albums_db import (
    delete_media_item_ids_from_albums_db,
)
from photos_drive.cli.commands.db.delete_media_items_without_album_id import (
    delete_media_items_without_album_id,
)
from photos_drive.cli.commands.db.dump import dump
from photos_drive.cli.commands.db.generate_embeddings import generate_embeddings
from photos_drive.cli.commands.db.initialize_map_cells_db import initialize_map_cells_db
from photos_drive.cli.commands.db.restore import restore
from photos_drive.cli.commands.db.set_media_item_date_taken_fields import (
    set_media_item_date_taken_fields,
)
from photos_drive.cli.commands.db.set_media_item_width_height_fields import (
    set_media_item_width_height_fields,
)

app = typer.Typer()
app.command()(dump)
app.command()(restore)
app.command()(delete_media_item_ids_from_albums_db)
app.command()(set_media_item_width_height_fields)
app.command()(set_media_item_date_taken_fields)
app.command()(delete_child_album_ids_from_albums_db)
app.command()(delete_media_items_without_album_id)
app.command()(initialize_map_cells_db)
app.command()(generate_embeddings)
