from ...shared.config.config import AddGPhotosConfigRequest, Config
from ...cli2.shared.inputs import (
    READ_ONLY_SCOPES,
    prompt_user_for_gphotos_credentials,
)


class AddGPhotosHandler:
    """A class that handles adding Google Photos account to config file from cli."""

    def add_gphotos(self, config: Config):
        """
        Adds Google Photos client to the config.

        Args:
            config (Config): The config object.
        """
        gphotos_account_name = self.__get_non_empty_name()

        print("Now, time to log into your Google account for read+write access\n")
        read_write_credentials = prompt_user_for_gphotos_credentials()

        print("Now, time to log into your Google account for read only access\n")
        read_only_credentials = prompt_user_for_gphotos_credentials(READ_ONLY_SCOPES)

        config.add_gphotos_config(
            AddGPhotosConfigRequest(
                name=gphotos_account_name,
                read_write_credentials=read_write_credentials,
                read_only_credentials=read_only_credentials,
            )
        )

        print("Successfully added your Google Photos account!")

    def __get_non_empty_name(self) -> str:
        """Prompts the user for a name and ensures it's not empty."""

        while True:
            name = input("Enter name of your Google Photos account: ")
            stripped_name = name.strip()

            if not stripped_name:
                print("Name cannot be empty. Please try again.")

            else:
                return stripped_name
