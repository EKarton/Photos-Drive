from ...shared.config.config import AddMongoDbConfigRequest, Config
from ...cli2.shared.inputs import prompt_user_for_mongodb_connection_string


class AddMongoDbHandler:
    """A class that handles adding a MongoDB account to the config file from cli."""

    def add_mongodb(self, config: Config):
        """
        Adds Mongo DB client to the config file.

        Args:
            config (Config): The config object.
        """
        name = self.__get_non_empty_name()

        read_write_connection_string = prompt_user_for_mongodb_connection_string(
            "Enter your read+write connection string: "
        )

        read_only_connection_string = prompt_user_for_mongodb_connection_string(
            "Enter your read only connection string: "
        )

        config.add_mongodb_config(
            AddMongoDbConfigRequest(
                name=name,
                read_write_connection_string=read_write_connection_string,
                read_only_connection_string=read_only_connection_string,
            )
        )

        print("Successfully added your Mongo DB account!")

    def __get_non_empty_name(self) -> str:
        """Prompts the user for a name and ensures it's not empty."""

        while True:
            name = input("Enter name of your Mongo DB account: ")
            stripped_name = name.strip()

            if not stripped_name:
                print("Name cannot be empty. Please try again.")

            else:
                return stripped_name
