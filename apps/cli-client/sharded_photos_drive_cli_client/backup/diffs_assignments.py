from typing import Dict
from bson import ObjectId

from ..shared.gphotos.clients_repository import GPhotosClientsRepository
from .processed_diffs import ProcessedDiff


class DiffsAssigner:
    def __init__(self, repo: GPhotosClientsRepository):
        self.__repo = repo

    def get_diffs_assignments(
        self, diffs: list[ProcessedDiff]
    ) -> Dict[ProcessedDiff, ObjectId]:
        """
        For every processed diffs with the "+" modifier, it will best assign a
        Google Photos account to upload the photo to.

        It will return a map of diffs with the "+" modifier with the best Google
        Photos account to upload to.

        Args:
            diffs (list[ProcessedDiff]): A list of processed diffs

        Returns:
            Dict[ProcessedDiff, ObjectId]: A map of processed diffs to GPhotos
                client ID.
        """
        client_id_to_space_remaining = {}
        for client_id, client in self.__repo.get_all_clients():
            space = client.get_storage_quota()
            client_id_to_space_remaining[client_id] = space.limit - space.usage

        diff_to_client_id: Dict[ProcessedDiff, ObjectId] = {}
        for diff in diffs:
            if diff.modifier != "+":
                continue

            space_needed = diff.file_size
            max_remaining_space = float("-inf")
            best_client_id = None

            for client_id, space_remaining in client_id_to_space_remaining.items():
                if space_needed > space_remaining:
                    continue

                if max_remaining_space < space_remaining:
                    max_remaining_space = space_remaining
                    best_client_id = client_id

            if not best_client_id:
                raise ValueError(
                    f"Cannot allocate {diff.file_path} to any GPhotos client"
                )

            diff_to_client_id[diff] = best_client_id
            client_id_to_space_remaining[best_client_id] -= space_needed

        return diff_to_client_id
