import typer

from sharded_photos_drive_cli_client.cli2.utils.config import config_callback

app = typer.Typer()


@app.command()
def add(ctx: typer.Context):
    print("add files handler")
    print(ctx)


app.callback()(config_callback)
