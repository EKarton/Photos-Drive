from configparser import ConfigParser
import json


class BackupHandler:
    """A class that handles backing up from cli."""

    def __init__(self, config_parser: ConfigParser = ConfigParser()):
        self.__config_parser = config_parser

    def backup(self, diffs_file_path: str, config_file_path: str):
        """
        Performs a backup based on the diff file.

        Args:
            diffs_file_path (str): The file path to the diffs.
            config_file_path (str): The file path to the config file.
        """
        self.__config_parser.read(config_file_path)

        with open(diffs_file_path, "r") as f:
            diffs_data = json.load(f)
        raise NotImplementedError("Backing up via CLI not supported yet.")
