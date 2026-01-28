from typing import Literal

from prettytable import HRuleStyle, PrettyTable, VRuleStyle
from termcolor import colored

from photos_drive.backup.diffs import Diff
from photos_drive.backup.processed_diffs import ProcessedDiff
from photos_drive.clean.clean_system import ItemsToDelete


def pretty_print_processed_diffs(processed_diffs: list[ProcessedDiff]):
    sorted_backup_diffs = sorted(processed_diffs, key=lambda obj: obj.file_path)
    table = PrettyTable()
    table.field_names = ["M", "File path", "File hash", "Location", "File size"]

    for diff in sorted_backup_diffs:
        color: Literal["green", "red"] = "green" if diff.modifier == "+" else "red"

        location_str = 'None'
        if diff.location:
            location_str = f'{diff.location.latitude}, {diff.location.longitude}'
        table.add_row(
            [
                colored(diff.modifier, color),
                colored(diff.file_path, color),
                colored(diff.file_hash.hex(), color),
                colored(location_str, color),
                colored(diff.file_size, color),
            ]
        )

    # Left align the columns
    table.align["M"] = "l"
    table.align["File path"] = "l"
    table.align["File hash"] = "l"
    table.align["Location"] = "l"
    table.align["File size"] = "l"

    # Remove the borders
    table.border = False
    table.hrules = HRuleStyle.NONE
    table.vrules = VRuleStyle.NONE

    print("============================================================")
    print("Changes")
    print("============================================================")
    print(table)

    # Get total number of + and -:
    total_additions = len([x for x in processed_diffs if x.modifier == '+'])
    total_deletions = len([x for x in processed_diffs if x.modifier == '-'])
    print('')
    print(f'Number of media items to add: {total_additions}')
    print(f'Number of media items to delete: {total_deletions}')
    print('')


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
    table.hrules = HRuleStyle.NONE
    table.vrules = VRuleStyle.NONE

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


def pretty_print_items_to_delete(items_to_delete: ItemsToDelete):
    table = PrettyTable()
    table.field_names = ["Type", "Client ID", "Object ID"]

    for album_id in items_to_delete.album_ids_to_delete:
        table.add_row(
            [
                colored('Album', "red"),
                colored(album_id.client_id, "red"),
                colored(album_id.object_id, 'red'),
            ]
        )

    for media_item_id in items_to_delete.media_item_ids_to_delete:
        table.add_row(
            [
                colored('Media Item', "red"),
                colored(media_item_id.client_id, "red"),
                colored(media_item_id.object_id, 'red'),
            ]
        )

    for gphotos_media_item_id in items_to_delete.gphotos_media_item_ids_to_delete:
        table.add_row(
            [
                colored('GPhotos Media Item', "red"),
                colored(gphotos_media_item_id.client_id, "red"),
                colored(gphotos_media_item_id.object_id, 'red'),
            ]
        )

    print("============================================================")
    print("Deletions")
    print("============================================================")
    print(table)
    print("Albums to delete:", len(items_to_delete.album_ids_to_delete))
    print("Media Items to delete:", len(items_to_delete.media_item_ids_to_delete))
    print(
        "GPhotos Media Items to delete:",
        len(items_to_delete.gphotos_media_item_ids_to_delete),
    )
