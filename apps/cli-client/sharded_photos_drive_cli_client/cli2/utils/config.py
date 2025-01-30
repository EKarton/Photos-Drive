from pymongo import MongoClient

from sharded_photos_drive_cli_client.shared.config.config import Config
from sharded_photos_drive_cli_client.shared.config.config_from_file import (
    ConfigFromFile,
)
from sharded_photos_drive_cli_client.shared.config.config_from_mongodb import (
    ConfigFromMongoDb,
)


def build_config_from_options(
    config_file: str | None, config_mongodb: str | None
) -> Config:
    '''
    Builds the config from cmd arg options

    Args:
        config_file (str): Path to the config file.
        config_mongodb (str): Connection string to the MongoDB that contains the config.

    Returns:
        Config: The config.
    '''
    if config_file:
        return ConfigFromFile(config_file)
    elif config_mongodb:
        return ConfigFromMongoDb(MongoClient(config_mongodb))
    else:
        raise ValueError('Unknown arg type')
