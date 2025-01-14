from ..shared.config.config import Config


class CleanHandler:
    """A class that handles cleaning up sharded google photos from cli."""

    def clean(self, config: Config):
        """
        Cleans the system.

        Args:
            config (Config): The config object
        """
        raise NotImplementedError("Cleaning up via CLI not supported yet.")
