from ...shared.config.config import Config

DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/photoslibrary.readonly",
    "https://www.googleapis.com/auth/photoslibrary.appendonly",
    "https://www.googleapis.com/auth/photoslibrary.edit.appcreateddata",
    "https://www.googleapis.com/auth/photoslibrary",
    "https://www.googleapis.com/auth/drive.photos.readonly",
]


class ReauthorizeHandler:
    """A class that handles adding Google Photos account to config file from cli."""

    def reauthorize(self, account_name: str, config: Config):
        """
        Reauthorizes existing Google Photos client in the config.

        Args:
            account_name (str): The name of the Google Photos client in the config.
            config (Config): The config object
        """
        raise NotImplementedError("This is not implemented yet")
