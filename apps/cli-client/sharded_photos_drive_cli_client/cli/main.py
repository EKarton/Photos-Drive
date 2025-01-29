import sys
import logging
import argparse

from pymongo.mongo_client import MongoClient

from sharded_photos_drive_cli_client.cli.config.reauthorize_mongodb_handler import (
    ReauthorizeMongoDbHandler,
)

from ..shared.config.config import Config
from ..shared.config.config_from_file import ConfigFromFile
from ..shared.config.config_from_mongodb import ConfigFromMongoDb
from .config.init_handler import InitHandler
from .config.add_gphotos_handler import AddGPhotosHandler
from .config.add_mongodb_handler import AddMongoDbHandler
from .config.reauthorize_gphotos_handler import ReauthorizeGPhotosHandler
from .add_file_hashes_handler import AddFileHashesHandler
from .usage_handler import UsageHandler
from .add_handler import AddHandler
from .delete_handler import DeleteHandler
from .clean_handler import CleanHandler
from .teardown_handler import TeardownHandler
from .sync_handler import SyncHandler


def main():
    parser = argparse.ArgumentParser(description="Sharded Google Photos CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Add subparser for the 'config' command
    config_parser = subparsers.add_parser("config")
    config_subparsers = config_parser.add_subparsers(dest="cmd_type")

    # Add subparser for the 'config init' command
    config_init_parser = config_subparsers.add_parser("init")
    __add_verbose_argument(config_init_parser)

    # Add subparser for the 'config add' command
    config_add_parser = config_subparsers.add_parser("add")
    config_add_subparsers = config_add_parser.add_subparsers(dest="account_type")

    # Add subparser for the 'config add gphotos' command
    config_add_gphotos_parser = config_add_subparsers.add_parser("gphotos")
    __add_config_argument(config_add_gphotos_parser)
    __add_verbose_argument(config_add_gphotos_parser)

    # Add subparser for the 'config add mongodb' command
    config_add_mongodb_parser = config_add_subparsers.add_parser("mongodb")
    __add_config_argument(config_add_mongodb_parser)
    __add_verbose_argument(config_add_mongodb_parser)

    # Add subparser for the 'config reauthorize gphotos' command
    config_reauthorize_parser = config_subparsers.add_parser("reauthorize")
    config_reauthorize_subparsers = config_reauthorize_parser.add_subparsers(
        dest="account_type"
    )
    config_reauthorize_gphotos_parsers = config_reauthorize_subparsers.add_parser(
        "gphotos"
    )
    config_reauthorize_gphotos_parsers.add_argument('id')
    __add_config_argument(config_reauthorize_gphotos_parsers)
    __add_verbose_argument(config_reauthorize_gphotos_parsers)

    # Add subparser for the 'config reauthorize mongodb' command
    config_reauthorize_mongodb_parsers = config_reauthorize_subparsers.add_parser(
        "mongodb"
    )
    config_reauthorize_mongodb_parsers.add_argument('id')
    __add_config_argument(config_reauthorize_mongodb_parsers)
    __add_verbose_argument(config_reauthorize_mongodb_parsers)

    # Add subparser for the 'add' command
    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("--path", required=True, help="Path to photos to add")
    add_parser.add_argument(
        "--parallelize_uploads",
        default=False,
        help="Parallelizes uploads to Google Photos [experimental]",
        action=argparse.BooleanOptionalAction,
    )
    __add_config_argument(add_parser)
    __add_verbose_argument(add_parser)

    # Add subparser for the 'delete' command
    delete_parser = subparsers.add_parser("delete")
    delete_parser.add_argument("--path", required=True, help="Path to photos to delete")
    __add_config_argument(delete_parser)
    __add_verbose_argument(delete_parser)

    # Add subparser for the 'sync' command`
    sync_parser = subparsers.add_parser('sync')
    sync_parser.add_argument(
        "--local_dir_path",
        required=True,
        help="Local directory path to photos to sync with",
    )
    sync_parser.add_argument(
        "--remote_albums_path",
        default='',
        help="Albums path in the remote to sync with",
    )
    sync_parser.add_argument(
        "--parallelize_uploads",
        default=False,
        help="Parallelizes uploads to Google Photos [experimental]",
        action=argparse.BooleanOptionalAction,
    )
    __add_config_argument(sync_parser)
    __add_verbose_argument(sync_parser)

    # Add subparser for the 'add-file-hashes' command
    add_file_hashes_parser = subparsers.add_parser('add-file-hashes')
    __add_config_argument(add_file_hashes_parser)
    __add_verbose_argument(add_file_hashes_parser)

    # Add subparser for the 'clean' command
    clean_parser = subparsers.add_parser("clean")
    __add_config_argument(clean_parser)
    __add_verbose_argument(clean_parser)

    # Add subparser for the 'teardown' command
    teardown_parser = subparsers.add_parser("teardown")
    __add_config_argument(teardown_parser)
    __add_verbose_argument(teardown_parser)

    usage_parser = subparsers.add_parser("usage")
    __add_config_argument(usage_parser)
    __add_verbose_argument(usage_parser)

    # Parse the arguments
    args = parser.parse_args()

    if args.command == "config":
        if args.cmd_type == "init":
            __set_logging(args.verbose)
            config_init_handler = InitHandler()
            config_init_handler.init()

        elif args.cmd_type == "add":
            if args.account_type == "gphotos":
                __set_logging(args.verbose)
                config = __build_config_based_on_args(args)
                config_add_handler = AddGPhotosHandler()
                config_add_handler.add_gphotos(config)

            elif args.account_type == "mongodb":
                __set_logging(args.verbose)
                config = __build_config_based_on_args(args)
                config_mongodb_handler = AddMongoDbHandler()
                config_mongodb_handler.add_mongodb(config)

            else:
                config_add_parser.print_help()
                exit(-1)

        elif args.cmd_type == "reauthorize":
            if args.account_type == 'gphotos':
                __set_logging(args.verbose)
                config = __build_config_based_on_args(args)
                reauthorize_gphotos_handler = ReauthorizeGPhotosHandler()
                reauthorize_gphotos_handler.run(args.id, config)

            elif args.account_type == 'mongodb':
                __set_logging(args.verbose)
                config = __build_config_based_on_args(args)
                reauthorize_mongodb_handler = ReauthorizeMongoDbHandler()
                reauthorize_mongodb_handler.run(args.id, config)

            else:
                config_add_parser.print_help()
                exit(-1)

        else:
            config_parser.print_help()
            exit(-1)

    elif args.command == "add":
        __set_logging(args.verbose)
        config = __build_config_based_on_args(args)
        add_handler = AddHandler()
        add_handler.add(args.path, config, args.parallelize_uploads)

    elif args.command == "delete":
        __set_logging(args.verbose)
        config = __build_config_based_on_args(args)
        delete_handler = DeleteHandler()
        delete_handler.delete(args.path, config)

    elif args.command == 'sync':
        __set_logging(args.verbose)
        config = __build_config_based_on_args(args)
        sync_handler = SyncHandler()
        sync_handler.sync(
            args.local_dir_path,
            args.remote_albums_path,
            config,
            args.parallelize_uploads,
        )

    elif args.command == 'add-file-hashes':
        __set_logging(args.verbose)
        config = __build_config_based_on_args(args)
        add_file_hashes_handler = AddFileHashesHandler()
        add_file_hashes_handler.run(config)

    elif args.command == "clean":
        __set_logging(args.verbose)
        config = __build_config_based_on_args(args)
        clean_handler = CleanHandler()
        clean_handler.clean(config)

    elif args.command == "teardown":
        __set_logging(args.verbose)
        config = __build_config_based_on_args(args)
        teardown_handler = TeardownHandler()
        teardown_handler.teardown(config)

    elif args.command == "usage":
        config = __build_config_based_on_args(args)
        usage_handler = UsageHandler()
        usage_handler.run(config)

    else:
        parser.print_help()
        exit(-1)


def __add_config_argument(parser: argparse.ArgumentParser):
    exclusive_group = parser.add_mutually_exclusive_group(required=True)
    exclusive_group.add_argument(
        "--config_file", type=str, help="Path to the configuration file"
    )
    exclusive_group.add_argument(
        "--config_mongodb",
        type=str,
        help="MongoDB connection string to the configuration",
    )


def __add_verbose_argument(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--verbose",
        default=False,
        help="Whether to show debug statements or not",
        action=argparse.BooleanOptionalAction,
    )


def __build_config_based_on_args(args: argparse.Namespace) -> Config:
    if args.config_file:
        return ConfigFromFile(args.config_file)
    elif args.config_mongodb:
        return ConfigFromMongoDb(MongoClient(args.config_mongodb))
    else:
        raise ValueError('Unknown arg type')


def __set_logging(isVerbose: bool):
    if isVerbose:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    else:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)


if __name__ == "__main__":
    main()
