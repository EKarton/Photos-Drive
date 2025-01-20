import os
from pymongo.mongo_client import MongoClient
from google.auth.transport.requests import AuthorizedSession

from ...shared.config.config import Config
from ...shared.config.config_from_file import ConfigFromFile
from ...shared.config.config_from_mongodb import ConfigFromMongoDb
from ...shared.mongodb.clients_repository import MongoDbClientsRepository
from ...shared.mongodb.albums_repository import AlbumsRepositoryImpl
from ...shared.gphotos.client import GPhotosClientV2
from .utils import prompt_user_for_mongodb_connection_string
from .utils import prompt_user_for_gphotos_credentials


class InitHandler:
    def init(self):
        """
        Initializes the config file.
        """
        # Step 0: Ask where to save config
        self.__prompt_welcome()
        config = self.__prompt_config()

        # Step 1: Ask for Mongo DB account
        print("First, let's log into your first Mongo DB account.")
        mongodb_name = self.__get_non_empty_name_for_mongodb()
        mongodb_connection_string = prompt_user_for_mongodb_connection_string()
        config.add_mongo_db_client(mongodb_name, mongodb_connection_string)

        # Step 2: Ask for Google Photo account
        print("Now it's time to log in to your first Google Photos account.")
        gphotos_name = self.__get_non_empty_name_for_gphotos()
        gphotos_credentials = prompt_user_for_gphotos_credentials()
        gphotos_session = AuthorizedSession(gphotos_credentials)
        gphotos_client = GPhotosClientV2(gphotos_name, gphotos_session)
        config.add_gphotos_client(gphotos_client)

        # Step 3: Create root album in Mongo DB account
        print("Perfect! Setting up your accounts...")
        mongodb_repo = MongoDbClientsRepository.build_from_config(config)
        albums_repo = AlbumsRepositoryImpl(mongodb_repo)
        root_album = albums_repo.create_album(
            album_name="", parent_album_id=None, child_album_ids=[], media_item_ids=[]
        )
        config.set_root_album_id(root_album.id)

        # Step 4: Save the config file
        if type(config) is ConfigFromFile:
            config.flush()
            print("Saved your config")

        # Step 5: Tell user how to add more MongoDB accounts / Google Photo accounts
        print(
            "Congratulations! You have set up a basic version of sharded_google_photos!"
        )
        print()
        print("Whenever you are running out of MongoDB space, you can always:")
        print("  1. Create a new MongoDB account from go/mongodb")
        print("  2. Run:")
        if type(config) is ConfigFromFile:
            print(
                "      sharded_google_photos config add mongodb ",
                "--config_file_path <file-path>",
            )
        else:
            print(
                "      sharded_google_photos config add mongodb ",
                "--config_mongodb <connection string>",
            )
        print("     and follow the prompts from there.")
        print()
        print(
            "Similarly, whenever you are running out of Google Photos space, ",
            "you can always:",
        )
        print("  1. Create a new Google Photos account from go/gphotos")
        print("  2. Run:")
        if type(config) is ConfigFromFile:
            print(
                "      sharded_google_photos config add gphotos ",
                "--config_file_path <file-path>",
            )
        else:
            print(
                "      sharded_google_photos config add gphotos ",
                "--config_mongodb <connection string>",
            )
        print("     and follow the prompts from there.")
        print()
        print("That's it! Have fun uploading photos!")

    def __prompt_welcome(self):
        print("Welcome!")
        print(
            "Before you get started with sharded_google_photos, you need the following:"
        )
        print(
            "\n  1. A place to store your config files (MongoDB or in a config file)."
        )
        print("\n  2. A place to store your photo metadata (MongoDB).")
        print("\n  3. A place to store your photos (Google Photos account).")
        print("")
        input("Press [enter] to continue")

    def __prompt_config(self) -> Config:
        config_type = self.__prompt_which_config_type()
        if config_type == 'mongodb':
            return self.__prompt_mongodb_config()
        elif config_type == 'file':
            return self.__prompt_config_file()
        else:
            raise ValueError(f"Unknown config type {config_type}")

    def __prompt_which_config_type(self) -> str:
        while True:
            print("Where do you want to store your config?")
            print("\n  1. Mongo DB (mongodb)")
            print("\n  2. File (file)")
            print(
                "\nThe config saves the accounts of where your photos metadata are, and"
                "\nthe accounts of where your photos are"
                "\n"
            )

            raw_input = input("Enter your choice:")
            user_input = raw_input.strip().lower()

            if user_input in ["mongodb", "1"]:
                return 'mongodb'
            elif user_input in ["file", "2"]:
                return 'file'
            else:
                print("Invalid input. Please enter \'mongodb\' or \'file\'")

    def __prompt_mongodb_config(self) -> ConfigFromMongoDb:
        connection_string = prompt_user_for_mongodb_connection_string()
        return ConfigFromMongoDb(MongoClient(connection_string))

    def __prompt_config_file(self) -> ConfigFromFile:
        while True:
            file_name = input("Enter file name:")
            file_path = os.path.join(os.getcwd(), file_name)

            if os.path.exists(file_path):
                print("File name already exists. Please try another file name.")
            else:
                return ConfigFromFile(file_path)

    def __get_non_empty_name_for_mongodb(self) -> str:
        """Prompts the user for a name and ensures it's not empty."""

        while True:
            name = input("Enter name of your first Mongo DB account: ")
            stripped_name = name.strip()

            if not stripped_name:
                print("Name cannot be empty. Please try again.")

            else:
                return stripped_name

    def __get_non_empty_name_for_gphotos(self) -> str:
        """Prompts the user for a name and ensures it's not empty."""

        while True:
            print(
                "Enter name of your first Google Photos account "
                + "(could be email address): "
            )
            name = input()
            stripped_name = name.strip()

            if not stripped_name:
                print("Name cannot be empty. Please try again.")

            else:
                return stripped_name
