import sys
import logging
import argparse

from .config.init_handler import InitHandler
from .config.add_gphotos_handler import AddGPhotosHandler
from .config.add_mongodb_handler import AddMongoDbHandler
from .config.reauthorize_handler import ReauthorizeHandler
from .add_handler import AddHandler
from .delete_handler import DeleteHandler
from .backup_handler import BackupHandler
from .clean_handler import CleanHandler
from .teardown_handler import TeardownHandler


def main():
    parser = argparse.ArgumentParser(description="Sharded Google Photos CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Add subparser for the 'config' command
    config_parser = subparsers.add_parser("config")
    config_subparsers = config_parser.add_subparsers(dest="cmd_type")

    # Add subparser for the 'config init' command
    config_init_parser = config_subparsers.add_parser("init")
    __add_config_file_argument(config_init_parser)
    __add_verbose_argument(config_init_parser)

    # Add subparser for the 'config add' command
    config_add_parser = config_subparsers.add_parser("add")
    config_add_subparsers = config_add_parser.add_subparsers(dest="account_type")

    # Add subparser for the 'config add gphotos' command
    config_add_gphotos_parser = config_add_subparsers.add_parser("gphotos")
    __add_config_file_argument(config_add_gphotos_parser)
    __add_verbose_argument(config_add_gphotos_parser)

    # Add subparser for the 'config add mongodb' command
    config_add_mongodb_parser = config_add_subparsers.add_parser("mongodb")
    __add_config_file_argument(config_add_mongodb_parser)
    __add_verbose_argument(config_add_mongodb_parser)

    # Add subparser for the 'config reauthorize gphotos' command
    config_reauthorize_parser = config_subparsers.add_parser("reauthorize")
    config_reauthorize_parser.add_argument(
        "--account_name", required=True, help="Name of the account"
    )
    __add_config_file_argument(config_reauthorize_parser)
    __add_verbose_argument(config_reauthorize_parser)

    # Add subparser for the 'add' command
    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("--path", required=True, help="Path to photos to add")
    __add_config_file_argument(add_parser)
    __add_verbose_argument(add_parser)

    # Add subparser for the 'delete' command
    delete_parser = subparsers.add_parser("delete")
    delete_parser.add_argument("--path", required=True, help="Path to photos to delete")
    __add_config_file_argument(delete_parser)
    __add_verbose_argument(delete_parser)

    # Add subparser for the 'backup' command
    backup_parser = subparsers.add_parser("backup")
    __add_diff_file_argument(backup_parser)
    __add_config_file_argument(backup_parser)
    __add_verbose_argument(backup_parser)

    # Add subparser for the 'clean' command
    clean_parser = subparsers.add_parser("clean")
    __add_config_file_argument(clean_parser)
    __add_verbose_argument(clean_parser)

    # Add subparser for the 'teardown' command
    teardown_parser = subparsers.add_parser("teardown")
    __add_config_file_argument(teardown_parser)
    __add_verbose_argument(teardown_parser)

    # Parse the arguments
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    else:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    if args.command == "config":
        if args.cmd_type == "init":
            config_init_handler = InitHandler()
            config_init_handler.init(args.config_file)

        elif args.cmd_type == "add":
            if args.account_type == "gphotos":
                config_add_handler = AddGPhotosHandler()
                config_add_handler.add_gphotos(args.config_file)

            elif args.account_type == "mongodb":
                config_mongodb_handler = AddMongoDbHandler()
                config_mongodb_handler.add_mongodb(args.config_file)

            else:
                config_add_parser.print_help()
                exit(-1)

        elif args.cmd_type == "reauthorize":
            reauthorize_handler = ReauthorizeHandler()
            reauthorize_handler.reauthorize(args.account_name, args.config_file)

        else:
            config_parser.print_help()
            exit(-1)

    elif args.command == "add":
        add_handler = AddHandler()
        add_handler.add(args.path, args.config_file)

    elif args.command == "delete":
        delete_handler = DeleteHandler()
        delete_handler.delete(args.path, args.config_file)

    elif args.command == "backup":
        backup_handler = BackupHandler()
        backup_handler.backup(args.diff_file, args.config_file)

    elif args.command == "clean":
        clean_handler = CleanHandler()
        clean_handler.clean(args.config_file)

    elif args.command == "teardown":
        teardown_handler = TeardownHandler()
        teardown_handler.teardown(args.config_file)

    else:
        parser.print_help()
        exit(-1)


def __add_config_file_argument(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--config_file", required=True, help="Path to the configuration file"
    )


def __add_diff_file_argument(parser: argparse.ArgumentParser):
    parser.add_argument("--diff_file", required=True, help="Path to the diff file")


def __add_verbose_argument(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--verbose",
        default=False,
        help="Whether to show debug statements or not",
        action=argparse.BooleanOptionalAction,
    )


if __name__ == "__main__":
    main()
