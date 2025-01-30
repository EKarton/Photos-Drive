from bson import ObjectId
from google.oauth2.credentials import Credentials

from ...shared.config.config import Config, GPhotosConfig, UpdateGPhotosConfigRequest
from ...cli2.shared.inputs import (
    READ_ONLY_SCOPES,
    READ_WRITE_SCOPES,
    prompt_user_for_non_empty_input_string,
    prompt_user_for_yes_no_answer,
    prompt_user_for_gphotos_credentials,
)


class ReauthorizeGPhotosHandler:
    """
    A class that handles reauthorizing existing Google Photos account in config file
    from cli.
    """

    def run(self, id_str: str, config: Config):
        """
        Reauthorizes existing Google Photos client in the config.

        Args:
            id_str (str): The GPhotos config id in the config.
            config (Config): The config object
        """
        id = ObjectId(id_str)
        cur_config = next(filter(lambda x: x.id == id, config.get_gphotos_configs()))
        new_name = self.__get_new_name(cur_config)
        new_read_write_credentials = self.__get_new_read_write_credentials()
        new_read_only_credentials = self.__get_new_read_only_credentials()

        has_change = (
            new_name is not None
            and new_read_write_credentials is not None
            and new_read_only_credentials is not None
        )

        if has_change:
            config.update_gphotos_config(
                UpdateGPhotosConfigRequest(
                    id=id,
                    new_name=new_name,
                    new_read_write_credentials=new_read_write_credentials,
                    new_read_only_credentials=new_read_only_credentials,
                )
            )
            print("Successfully updated gphotos config {id_str}")
        else:
            print("No change")

    def __get_new_name(self, cur_config: GPhotosConfig) -> str | None:
        print(f"The account name is {cur_config.name}")
        if not prompt_user_for_yes_no_answer("Do you want to change the name? (Y/N): "):
            return None

        return prompt_user_for_non_empty_input_string("Enter new name: ")

    def __get_new_read_write_credentials(self) -> Credentials | None:
        if not prompt_user_for_yes_no_answer(
            "Do you want to change the read+write credentials? (Y/N): "
        ):
            return None

        return prompt_user_for_gphotos_credentials(READ_WRITE_SCOPES)

    def __get_new_read_only_credentials(self) -> Credentials | None:
        if not prompt_user_for_yes_no_answer(
            "Do you want to change the read-only credentials? (Y/N): "
        ):
            return None

        return prompt_user_for_gphotos_credentials(READ_ONLY_SCOPES)
