import typer
from .generate_embeddings import generate_embeddings
from .set_media_item_date_taken_fields import (
    set_media_item_date_taken_fields,
)
from .set_media_item_width_height_fields import (
    set_media_item_width_height_fields,
)
from .dump import dump
from .restore import restore
from .delete_media_item_ids_from_albums_db import delete_media_item_ids_from_albums_db
from .delete_child_album_ids_from_albums_db import delete_child_album_ids_from_albums_db
from .delete_media_items_without_album_id import delete_media_items_without_album_id
from .initialize_map_cells_db import initialize_map_cells_db
from .copy_date_taken_and_location_to_vector_store import (
    copy_date_taken_and_location_to_vector_store,
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
app.command()(copy_date_taken_and_location_to_vector_store)
