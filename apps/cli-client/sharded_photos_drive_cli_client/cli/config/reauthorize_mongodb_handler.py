from bson import ObjectId

from ...shared.config.config import (
    Config,
    MongoDbConfig,
    UpdateMongoDbConfigRequest,
)
from ...cli2.shared.inputs import (
    prompt_user_for_non_empty_input_string,
    prompt_user_for_yes_no_answer,
    prompt_user_for_mongodb_connection_string,
)


class ReauthorizeMongoDbHandler:
    """
    A class that handles reauthorizing existing MongoDB account in config file
    from cli.
    """

    def run(self, id_str: str, config: Config):
        """
        Reauthorizes existing MongoDB client in the config.

        Args:
            id (str): The MongoDB config id in the config.
            config (Config): The config object
        """
        id = ObjectId(id_str)
        cur_config = next(filter(lambda x: x.id == id, config.get_mongodb_configs()))
        new_name = self.__get_new_name(cur_config)
        new_read_write_connection_string = self.__get_new_read_write_connection_string()
        new_read_only_connection_string = self.__get_new_read_only_connection_string()

        has_change = (
            new_name is not None
            and new_read_write_connection_string is not None
            and new_read_only_connection_string is not None
        )

        if has_change:
            config.update_mongodb_config(
                UpdateMongoDbConfigRequest(
                    id=id,
                    new_name=new_name,
                    new_read_write_connection_string=new_read_write_connection_string,
                    new_read_only_connection_string=new_read_only_connection_string,
                )
            )
            print("Successfully updated mongodb config {id_str}")
        else:
            print("No change")

    def __get_new_name(self, cur_config: MongoDbConfig) -> str | None:
        print(f"The account name is {cur_config.name}")
        if not prompt_user_for_yes_no_answer("Do you want to change the name? (Y/N): "):
            return None

        return prompt_user_for_non_empty_input_string("Enter new name: ")

    def __get_new_read_write_connection_string(self) -> str | None:
        if not prompt_user_for_yes_no_answer(
            "Do you want to change the read+write connection string? (Y/N): "
        ):
            return None

        return prompt_user_for_mongodb_connection_string(
            "Enter your new read+write connection string: "
        )

    def __get_new_read_only_connection_string(self) -> str | None:
        if not prompt_user_for_yes_no_answer(
            "Do you want to change the read+only connection string? (Y/N): "
        ):
            return None

        return prompt_user_for_mongodb_connection_string(
            "Enter your new read+only connection string: "
        )
