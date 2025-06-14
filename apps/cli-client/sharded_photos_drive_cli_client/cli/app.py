import typer

from sharded_photos_drive_cli_client.cli.commands import config
from sharded_photos_drive_cli_client.cli.commands import db
from sharded_photos_drive_cli_client.cli.commands import add
from sharded_photos_drive_cli_client.cli.commands import clean
from sharded_photos_drive_cli_client.cli.commands import delete
from sharded_photos_drive_cli_client.cli.commands import sync
from sharded_photos_drive_cli_client.cli.commands import teardown
from sharded_photos_drive_cli_client.cli.commands import usage


def build_app() -> typer.Typer:
    app = typer.Typer()

    app.add_typer(config.app, name="config")
    app.add_typer(db.app, name="db")
    app.add_typer(add.app)
    app.add_typer(delete.app)
    app.add_typer(sync.app)
    app.add_typer(clean.app)
    app.add_typer(teardown.app)
    app.add_typer(usage.app)

    return app


def main():
    build_app()()


if __name__ == '__main__':
    build_app()()
