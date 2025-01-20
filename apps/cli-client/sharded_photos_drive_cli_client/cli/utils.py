import os
from typing import Literal
from prettytable import PrettyTable, NONE
from termcolor import colored

from ..backup.diffs import Diff
from ..shared.gphotos.valid_file_extensions import MEDIA_ITEM_FILE_EXTENSIONS


def get_diffs_from_path(path: str) -> list[str]:
    """
    Returns a list of file paths that are under a path.

    If the path points to a media item, it will return the file path of that media item.

    If a path points to a directory, it will return a list of file paths to all media
    items under that directory.

    Args:
        path (str): A generic path

    Raises:
        ValueError if the path does not exist

    Returns:
        list(str): A list of file paths of media items it found.
    """
    if os.path.isdir(path):
        return get_diffs_from_dir_path(path)

    if os.path.isfile(path):
        if not path.lower().endswith(MEDIA_ITEM_FILE_EXTENSIONS):
            raise ValueError(f"File {path} is not an image or video")

        return [path]

    raise ValueError(f"File {path} does not exist")


def get_diffs_from_dir_path(dir_path: str) -> list[str]:
    """
    Returns a list of file paths of media items that are under a directory.

    Args:
        dir_path (str): A directory path

    Returns:
        list(str): A list of file paths to all media items under that directory.
    """
    diffs = []

    for root, _, files in os.walk(dir_path):
        for file in files:
            if not file.lower().endswith(MEDIA_ITEM_FILE_EXTENSIONS):
                continue

            # Construct the relative path
            relative_path = os.path.join(".", os.path.relpath(os.path.join(root, file)))

            # Replace '\' with '/' for consistency (from Windows to Unix-based)
            formatted_path = relative_path.replace(os.sep, "/")

            diffs.append(formatted_path)

    return diffs


def pretty_print_diffs(backup_diffs: list[Diff]):
    sorted_backup_diffs = sorted(backup_diffs, key=lambda obj: obj.file_path)
    table = PrettyTable()
    table.field_names = ["M", "File path"]

    for diff in sorted_backup_diffs:
        color: Literal["green", "red"] = "green" if diff.modifier == "+" else "red"
        table.add_row([colored(diff.modifier, color), colored(diff.file_path, color)])

    # Left align the columns
    table.align["M"] = "l"
    table.align["File path"] = "l"

    # Remove the borders
    table.border = False
    table.hrules = NONE
    table.vrules = NONE

    print("============================================================")
    print("Changes")
    print("============================================================")
    print(table)

    # Get total number of + and -:
    total_additions = len([x for x in backup_diffs if x.modifier == '+'])
    total_deletions = len([x for x in backup_diffs if x.modifier == '-'])
    print('')
    print(f'Number of media items to add: {total_additions}')
    print(f'Number of media items to delete: {total_deletions}')
    print('')


def prompt_user_to_confirm() -> bool:
    while True:
        raw_input = input("Is this correct? (yes / no): ")
        user_input = raw_input.strip().lower()

        if user_input in ["yes", "y"]:
            return True
        elif user_input in ["no", "n"]:
            return False
        else:
            print("Invalid input. Please enter \'y\' or \'n\'")
