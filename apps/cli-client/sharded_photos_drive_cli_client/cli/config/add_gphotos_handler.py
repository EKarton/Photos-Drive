from google.auth.transport.requests import AuthorizedSession

from ...shared.config.config_from_file import ConfigFromFile
from ...shared.gphotos.client import GPhotosClientV2
from .utils import prompt_user_for_gphotos_credentials


class AddGPhotosHandler:
    """A class that handles adding Google Photos account to config file from cli."""

    def add_gphotos(self, config_file_path: str):
        """
        Adds Google Photos client to the config.

        Args:
            config_file_path (str): The file path to the config file.
        """
        config = ConfigFromFile(config_file_path)

        gphotos_account_name = self.__get_non_empty_name()
        gphotos_credentials = prompt_user_for_gphotos_credentials()
        gphotos_session = AuthorizedSession(gphotos_credentials)
        gphotos_client = GPhotosClientV2(gphotos_account_name, gphotos_session)

        config.add_gphotos_client(gphotos_client)
        config.flush()

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
