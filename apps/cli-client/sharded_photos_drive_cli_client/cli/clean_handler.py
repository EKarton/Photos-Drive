from configparser import ConfigParser


class CleanHandler:
    """A class that handles cleaning up sharded google photos from cli."""

    def __init__(self, config_parser: ConfigParser = ConfigParser()):
        self.__config_parser = config_parser

    def clean(self, config_file_path: str):
        """
        Cleans the system.

        Args:
            config_file_path (str): The file path to the config file.
        """
        self.__config_parser.read(config_file_path)
        raise NotImplementedError("Cleaning up via CLI not supported yet.")
