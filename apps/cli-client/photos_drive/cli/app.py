import typer

from photos_drive.cli.commands import (
    add,
    clean,
    config,
    db,
    delete,
    llm,
    sync,
    teardown,
    usage,
)


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
    app.add_typer(llm.app)

    return app


def main():
    build_app()()


if __name__ == '__main__':
    build_app()()
