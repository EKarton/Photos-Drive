import configparser

from google_auth_oauthlib.flow import InstalledAppFlow

DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/photoslibrary.readonly",
    "https://www.googleapis.com/auth/photoslibrary.appendonly",
    "https://www.googleapis.com/auth/photoslibrary.edit.appcreateddata",
    "https://www.googleapis.com/auth/photoslibrary",
    "https://www.googleapis.com/auth/drive.photos.readonly",
]


class ReauthorizeHandler:
    """A class that handles adding Google Photos account to config file from cli."""

    def reauthorize(self, account_name: str, config_file_path: str):
        """
        Reauthorizes existing Google Photos client in the config.

        Args:
            account_name (str): The name of the Google Photos client in the config file.
            config_file_path (str): The file path to the config file.
        """
        config = configparser.ConfigParser()
        config.read(config_file_path)

        gphotos_client_id = None
        for section_id in config.sections():
            if config.get(section_id, "type") != "gphotos":
                continue

            if config.get(section_id, "name") != account_name:
                continue

            gphotos_client_id = section_id

        if not gphotos_client_id:
            raise ValueError(
                f"Cannot find Google Photos account with name {account_name}"
            )

        iaflow: InstalledAppFlow = InstalledAppFlow.from_client_config(
            client_config={
                "web": {
                    "client_id": config.get(gphotos_client_id, "client_id"),
                    "client_secret": config.get(gphotos_client_id, "client_secret"),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=DEFAULT_SCOPES,
        )
        iaflow.run_local_server(
            authorization_prompt_message=f"Please visit this URL to authenticate: {{url}}",
            success_message="The auth flow is complete; you may close this window.",
            open_browser=False,
        )
        credentials = iaflow.credentials

        if credentials.refresh_token:
            config.set(gphotos_client_id, "refresh_token", credentials.refresh_token)

        if credentials.token:
            config.set(gphotos_client_id, "token", credentials.token)

        if credentials.client_id:
            config.set(gphotos_client_id, "client_id", credentials.client_id)

        if credentials.client_secret:
            config.set(gphotos_client_id, "client_secret", credentials.client_secret)

        if credentials.token_uri:
            config.set(gphotos_client_id, "token_uri", credentials.token_uri)

        with open(config_file_path, "w") as configfile:
            config.write(configfile)

        print("Successfully re-authenticated your Google Photos account!")
