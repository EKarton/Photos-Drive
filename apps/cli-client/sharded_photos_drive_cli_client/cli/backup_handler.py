from ..shared.config.config import Config


class BackupHandler:
    """A class that handles backing up from cli."""

    def backup(self, diffs_file_path: str, config: Config):
        """
        Performs a backup based on the diff file.

        Args:
            diffs_file_path (str): The file path to the diffs.
            config (Config): The config.
        """
        raise NotImplementedError("Backing up via CLI not supported yet.")
