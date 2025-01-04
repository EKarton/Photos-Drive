import os

from google.auth.transport.requests import AuthorizedSession

from ...shared.config.config_from_file import ConfigFromFile
from ...shared.mongodb.clients_repository import MongoDbClientsRepository
from ...shared.mongodb.albums_repository import AlbumsRepositoryImpl
from ...shared.gphotos.client import GPhotosClientV2
from .utils import prompt_user_for_mongodb_connection_string
from .utils import prompt_user_for_gphotos_credentials


class InitHandler:
    def init(self, config_file_path: str):
        """
        Initializes the config file.

        Args:
            config_file_path (str): The file path to the config file.
        """
        if os.path.exists(config_file_path):
            print(f"File {config_file_path} already exists!")
            self.__confirm_deletion_of_existing_config_file(config_file_path)

        # Step 0: Prompt user about requirements
        self.__confirm_requirements()

        # Step 1: Ask for Mongo DB account
        print("First, let's log into your first Mongo DB account.")
        mongodb_name = self.__get_non_empty_name_for_mongodb()
        mongodb_connection_string = prompt_user_for_mongodb_connection_string()

        # Step 2: Ask for Google Photo account
        print("Now it's time to log in to your first Google Photos account.")
        gphotos_name = self.__get_non_empty_name_for_gphotos(mongodb_name)
        gphotos_credentials = prompt_user_for_gphotos_credentials()
        gphotos_session = AuthorizedSession(gphotos_credentials)
        gphotos_client = GPhotosClientV2(gphotos_name, gphotos_session)

        # Step 3: Create the config file
        config = ConfigFromFile(config_file_path)
        config.add_gphotos_client(gphotos_client)
        config.add_mongo_db_client(mongodb_name, mongodb_connection_string)

        # Step 3: Create root album in Mongo DB account
        print("Perfect! Setting up your accounts...")
        mongodb_repo = MongoDbClientsRepository.build_from_config(config)
        albums_repo = AlbumsRepositoryImpl(mongodb_repo)
        root_album = albums_repo.create_album(
            album_name="", parent_album_id=None, child_album_ids=[], media_item_ids=[]
        )
        config.set_root_album_id(root_album.id)

        # Step 4: Save the config file
        config.flush()
        print(f"Saved your config file to {config_file_path}")

        # Step 5: Tell user how to add more MongoDB accounts or more Google Photo accounts
        print(
            "Congratulations! You have set up a basic version of sharded_google_photos!"
        )
        print()
        print("Whenever you are running out of MongoDB space, you can always:")
        print("  1. Create a new MongoDB account from go/mongodb")
        print("  2. Run:")
        print(
            "      sharded_google_photos config add mongodb --config_file {config_file_path}"
        )
        print("    and follow the prompts from there.")
        print()
        print(
            "Similarly, whenever you are running out of Google Photos space, you can always:"
        )
        print("  1. Create a new Google Photos account from go/gphotos")
        print("  2. Run:")
        print(
            "      sharded_google_photos config add gphotos --config_file {config_file_path}"
        )
        print("    and follow the prompts from there.")
        print()
        print("That's it! Have fun uploading photos!")

    def __confirm_requirements(self):
        print("Welcome!")
        print(
            "Before you get started with sharded_google_photos, you need the following:"
        )
        print("\n  1. A Mongo DB account.")
        print("\n  2. A Google Photos account.\n")

        while True:
            raw_input = input("Do you have the following above? [Yes/Y] or [No/N]: ")
            user_input = raw_input.strip().lower()

            if user_input in ["yes", "y"]:
                return True
            elif user_input in ["no", "n"]:
                return False
            else:
                print("Invalid input. Please enter Yes/Y or No/N.")

    def __confirm_deletion_of_existing_config_file(self, config_file_path: str):
        while True:
            raw_input = input("Do you want to delete the file? [Yes/Y] or [No/N]: ")
            user_input = raw_input.strip().lower()

            if user_input in ["yes", "y"]:
                os.remove(config_file_path)
                return
            elif user_input in ["no", "n"]:
                raise ValueError("Terminated deleting existing config file.")
            else:
                print("Invalid input. Please enter Yes/Y or No/N.")

    def __get_non_empty_name_for_mongodb(self) -> str:
        """Prompts the user for a name and ensures it's not empty."""

        while True:
            name = input("Enter name of your first Mongo DB account: ")
            stripped_name = name.strip()

            if not stripped_name:
                print("Name cannot be empty. Please try again.")

            else:
                return stripped_name

    def __get_non_empty_name_for_gphotos(self, mongodb_name: str) -> str:
        """Prompts the user for a name and ensures it's not empty."""

        while True:
            name = input(
                "Enter name of your first Google Photos account (could be email address): "
            )
            stripped_name = name.strip()

            if not stripped_name:
                print("Name cannot be empty. Please try again.")

            if mongodb_name == stripped_name:
                print(
                    "Name cannot be the same as your Mongo DB account. Please try again."
                )

            else:
                return stripped_name
