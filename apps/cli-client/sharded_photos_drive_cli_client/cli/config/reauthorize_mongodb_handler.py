from ...shared.config.config import Config


class ReauthorizeMongoDbHandler:
    """
    A class that handles reauthorizing existing MongoDB account in config file
    from cli.
    """

    def run(self, id: str, config: Config):
        """
        Reauthorizes existing MongoDB client in the config.

        Args:
            id (str): The MongoDB config id in the config.
            config (Config): The config object
        """
        print(id, config)
        raise NotImplementedError("This is not implemented yet")
