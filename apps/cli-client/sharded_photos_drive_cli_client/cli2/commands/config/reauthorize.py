import logging
import typer

from sharded_photos_drive_cli_client.cli2.utils.typer import (
    createMutuallyExclusiveGroup,
)

logger = logging.getLogger(__name__)

app = typer.Typer()
config_exclusivity_callback = createMutuallyExclusiveGroup(2)


@app.command()
def gphotos(ctx: typer.Context):
    print('config reauthorize gphotos')
    print(ctx)


@app.command()
def mongodb(ctx: typer.Context):
    print("config reauthorize mongodb")
    print(ctx)
