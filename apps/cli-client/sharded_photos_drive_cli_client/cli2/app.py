import typer

from sharded_photos_drive_cli_client.cli2.commands import config
from sharded_photos_drive_cli_client.cli2.commands import (
    add_album_id_fields_to_media_items,
)
from sharded_photos_drive_cli_client.cli2.commands import add
from sharded_photos_drive_cli_client.cli2.commands import clean
from sharded_photos_drive_cli_client.cli2.commands import delete
from sharded_photos_drive_cli_client.cli2.commands import sync
from sharded_photos_drive_cli_client.cli2.commands import teardown
from sharded_photos_drive_cli_client.cli2.commands import usage


def build_app() -> typer.Typer:
    app = typer.Typer()

    app.add_typer(config.app, name="config")
    app.add_typer(add.app)
    app.add_typer(delete.app)
    app.add_typer(sync.app)
    app.add_typer(clean.app)
    app.add_typer(teardown.app)
    app.add_typer(usage.app)
    app.add_typer(add_album_id_fields_to_media_items.app)

    return app


def main():
    build_app()()


if __name__ == '__main__':
    build_app()()
