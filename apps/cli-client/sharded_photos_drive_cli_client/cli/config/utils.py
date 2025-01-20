import getpass
from typing import Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from pymongo.mongo_client import MongoClient

DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/photoslibrary.readonly",
    "https://www.googleapis.com/auth/photoslibrary.appendonly",
    "https://www.googleapis.com/auth/photoslibrary.edit.appcreateddata",
    "https://www.googleapis.com/auth/photoslibrary",
    "https://www.googleapis.com/auth/drive.photos.readonly",
]


def prompt_user_for_mongodb_connection_string() -> str:
    """
    Prompts the user multiple times for the MongoDB connection string.
    It will test the connection out, and will ask again if it fails.

    Returns:
        str: The connection string
    """

    mongodb_connection_string = None
    while True:
        print(
            "Enter your MongoDB connection string",
        )
        mongodb_connection_string = getpass.getpass()
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
    scopes: list[str] = DEFAULT_SCOPES,
) -> Credentials:
    """
    Prompts the user to enter Google Photos account.

    Args:
        scopes (list[str]): A list of scopes, defaulted to DEFAULT_SCOPES.

    Returns:
        Credentials: A set of credentials obtained.
    """
    credentials: Optional[Credentials] = None
    is_login_successful = False
    while not is_login_successful:
        client_id = get_non_empty_client_id()
        client_secret = get_non_empty_client_secret()

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
            is_login_successful = True
        except Exception as e:
            print(f'Error: ${e}')
            print("Failure in authenticating to Google Photos account. Try again.")
            credentials = None
            is_login_successful = False

    if not credentials:
        raise ValueError("Credentials is empty!")

    return credentials


def get_non_empty_client_id() -> str:
    """Prompts the user for a name and ensures it's not empty."""

    while True:
        value = getpass.getpass("Enter Google Photos Client ID: ")
        value = value.strip()

        if not value:
            print("Client ID cannot be empty. Please try again.")
        else:
            return value


def get_non_empty_client_secret() -> str:
    while True:
        value = getpass.getpass("Enter Google Photos client secret: ")
        value = value.strip()

        if not value:
            print("Client secret cannot be empty. Please try again.")
        else:
            return value
