import getpass
from typing import Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from pymongo.mongo_client import MongoClient

'''
Scopes for read+write access.
Refer to https://developers.google.com/photos/overview/authorization#library-api-scopes
'''
READ_WRITE_SCOPES = [
    "https://www.googleapis.com/auth/photoslibrary.readonly",
    "https://www.googleapis.com/auth/photoslibrary.appendonly",
    "https://www.googleapis.com/auth/drive.photos.readonly",
]

'''
Scopes for read-only access.
Refer to https://developers.google.com/photos/overview/authorization#library-api-scopes
'''
READ_ONLY_SCOPES = [
    "https://www.googleapis.com/auth/photoslibrary.readonly",
    "https://www.googleapis.com/auth/drive.photos.readonly",
]


def prompt_user_for_mongodb_connection_string(prompt_text: str) -> str:
    """
    Prompts the user multiple times for the MongoDB connection string.
    It will test the connection out, and will ask again if it fails.

    Returns:
        str: The connection string
    """

    mongodb_connection_string = None
    while True:
        mongodb_connection_string = prompt_user_for_non_empty_password(prompt_text)
        try:
            mongodb_client: MongoClient = MongoClient(
                mongodb_connection_string,
            )
            mongodb_client.admin.command("ping")
            return mongodb_connection_string
        except Exception as e:
            print(f'Error: ${e}')
            print("Failed to connect to Mongo DB with connection string. Try again.")


def prompt_user_for_gphotos_credentials(
    scopes: list[str] = READ_WRITE_SCOPES,
) -> Credentials:
    """
    Prompts the user to enter Google Photos account.

    Args:
        scopes (list[str]): A list of scopes, defaulted to READ_WRITE_SCOPES.

    Returns:
        Credentials: A set of credentials obtained.
    """
    credentials: Optional[Credentials] = None
    is_login_successful = False
    while not is_login_successful:
        client_id = prompt_user_for_non_empty_password(
            "Enter Google Photos Client ID: "
        )
        client_secret = prompt_user_for_non_empty_password(
            "Enter Google Photos client secret: "
        )

        try:
            iaflow: InstalledAppFlow = InstalledAppFlow.from_client_config(
                client_config={
                    "web": {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                },
                scopes=scopes,
            )
            message = "Please visit this URL to authenticate: {url}"
            iaflow.run_local_server(
                authorization_prompt_message=message,
                success_message="The auth flow is complete; you may close this window.",
                open_browser=False,
            )

            credentials = iaflow.credentials
            if not credentials:
                raise ValueError("Credentials is None!")

            if not credentials.scopes:
                raise ValueError("Missing scopes! Please try again.")

            chosen_scopes: set[str] = set(credentials.scopes)
            required_scopes: set[str] = set(scopes)
            if not required_scopes.issubset(chosen_scopes):
                raise ValueError(
                    f"Missing scopes! Got {chosen_scopes}, needed {required_scopes}"
                )

            is_login_successful = True
        except Exception as e:
            print(f'Error: ${e}')
            print("Failure in authenticating to Google Photos account. Try again.")
            credentials = None
            is_login_successful = False

    if not credentials:
        raise ValueError("Credentials is empty!")

    return credentials


def prompt_user_for_non_empty_password(prompt_text: str) -> str:
    """Prompts the user for a password and ensures it's not empty."""
    while True:
        value = getpass.getpass(prompt_text)
        value = value.strip()

        if not value:
            print("Input cannot be empty. Please try again.")
        else:
            return value


def prompt_user_for_non_empty_input_string(prompt_text: str) -> str:
    """Prompts the user for a string and ensures it's not empty."""

    while True:
        name = input(prompt_text)
        stripped_name = name.strip()

        if not stripped_name:
            print("Input cannot be empty. Please try again.")

        else:
            return stripped_name


def prompt_user_for_yes_no_answer(prompt_text: str) -> bool:
    while True:
        raw_input = input(prompt_text)
        user_input = raw_input.strip().lower()

        if user_input in ["yes", "y"]:
            return True
        elif user_input in ["no", "n"]:
            return False
        else:
            print("Invalid input. Please enter \'y\' or \'n\'")
