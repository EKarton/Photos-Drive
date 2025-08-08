import logging

import typer
from typing_extensions import Annotated

from photos_drive.cli.shared.config import build_config_from_options
from photos_drive.cli.shared.logging import setup_logging
from photos_drive.cli.shared.typer import (
    createMutuallyExclusiveGroup,
)
from photos_drive.shared.metadata.mongodb.clients_repository_impl import (
    MongoDbClientsRepository,
)

logger = logging.getLogger(__name__)

app = typer.Typer()
config_exclusivity_callback = createMutuallyExclusiveGroup(2)


@app.command()
def delete_media_item_ids_from_albums_db(
    config_file: Annotated[
        str | None,
        typer.Option(
            "--config-file",
            help="Path to config file",
            callback=config_exclusivity_callback,
        ),
    ] = None,
    config_mongodb: Annotated[
        str | None,
        typer.Option(
            "--config-mongodb",
            help="Connection string to a MongoDB account that has the configs",
            is_eager=False,
            callback=config_exclusivity_callback,
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            help="Whether to show all logging debug statements or not",
        ),
    ] = False,
):
    setup_logging(verbose)

    logger.debug(
        "Called db delete-media-item-ids-from-albums-db handler with args:\n"
        + f" config_file: {config_file}\n"
        + f" config_mongodb={config_mongodb}\n"
        + f" verbose={verbose}"
    )

    # Set up the repos
    config = build_config_from_options(config_file, config_mongodb)
    mongodb_clients_repo = MongoDbClientsRepository.build_from_config(config)

    for _, client in mongodb_clients_repo.get_all_clients():
        for obj in client['photos_drive']['albums'].find({}):
            filter_obj = {"_id": obj["_id"]}
            update_obj = {"$unset": {"media_item_ids": 1}}
            client['photos_drive']['albums'].update_one(
                filter=filter_obj, update=update_obj
            )
