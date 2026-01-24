from photos_drive.shared.utils.mongodb.get_free_space import get_free_space
from typing import Any, Mapping, cast

from bson.objectid import ObjectId
import pymongo

from photos_drive.shared.core.albums.album_id import (
    AlbumId,
    album_id_to_string,
    parse_string_to_album_id,
)
from photos_drive.shared.core.albums.albums import Album
from photos_drive.shared.core.albums.repository.base import (
    AlbumsRepository,
    UpdateAlbumRequest,
    UpdatedAlbumFields,
    logger,
)
from photos_drive.shared.core.clients.mongodb import (
    MongoDbClientsRepository,
)


class MongoDBAlbumsRepository(AlbumsRepository):
    """Implementation class for AlbumsRepository."""

    def __init__(
        self,
        client_id: ObjectId,
        mongodb_clients_repository: MongoDbClientsRepository,
    ):
        """
        Creates a AlbumsRepository

        Args:
            client_id (ObjectId): The client ID that this repo is connected to.
            mongodb_clients_repository (MongoDbClientsRepository): A repo of mongo db
                clients that stores albums.
        """
        self._client_id = client_id
        self._mongodb_clients_repository = mongodb_clients_repository
        self._mongodb_client = self._mongodb_clients_repository.get_client_by_id(
            client_id
        )
        self._collection = self._mongodb_client["photos_drive"]["albums"]

    def get_client_id(self) -> ObjectId:
        return self._client_id

    def get_available_free_space(self) -> int:
        return get_free_space(self._mongodb_client)

    def get_album_by_id(self, id: AlbumId) -> Album:
        if id.client_id != self._client_id:
            raise ValueError(f"Album {id} belongs to a different client")

        session = self._mongodb_clients_repository.get_session_for_client_id(
            self._client_id
        )
        raw_item = cast(
            dict,
            self._collection.find_one({"_id": id.object_id}, session=session),
        )

        if raw_item is None:
            raise ValueError(f"Album {id} does not exist!")

        return self.__parse_raw_document_to_album_obj(self._client_id, raw_item)

    def get_all_albums(self) -> list[Album]:
        albums: list[Album] = []
        session = self._mongodb_clients_repository.get_session_for_client_id(
            self._client_id,
        )
        for doc in self._collection.find(filter={}, session=session):
            raw_item = cast(dict, doc)
            album = self.__parse_raw_document_to_album_obj(self._client_id, raw_item)
            albums.append(album)

        return albums

    def create_album(
        self,
        album_name: str,
        parent_album_id: AlbumId | None,
    ) -> Album:
        session = self._mongodb_clients_repository.get_session_for_client_id(
            self._client_id,
        )

        result = self._collection.insert_one(
            document={
                "name": album_name,
                "parent_album_id": (
                    album_id_to_string(parent_album_id)
                    if parent_album_id is not None
                    else None
                ),
            },
            session=session,
        )

        return Album(
            id=AlbumId(client_id=self._client_id, object_id=result.inserted_id),
            name=album_name,
            parent_album_id=parent_album_id,
        )

    def delete_album(self, id: AlbumId):
        if id.client_id != self._client_id:
            raise ValueError(f"Album {id} belongs to a different client")

        session = self._mongodb_clients_repository.get_session_for_client_id(
            self._client_id,
        )
        result = self._collection.delete_one(
            filter={"_id": id.object_id},
            session=session,
        )

        if result.deleted_count != 1:
            raise ValueError(f"Unable to delete album: Album {id} not found")

    def delete_many_albums(self, ids: list[AlbumId]):
        if len(ids) == 0:
            return

        object_ids: list[ObjectId] = []
        for id in ids:
            if id.client_id != self._client_id:
                raise ValueError(
                    f"Album {id} belongs to a different client {id.client_id} "
                    + f"vs {self._client_id}"
                )
            object_ids.append(id.object_id)

        session = self._mongodb_clients_repository.get_session_for_client_id(
            self._client_id,
        )
        result = self._collection.delete_many(
            filter={"_id": {"$in": object_ids}},
            session=session,
        )

        if result.deleted_count != len(object_ids):
            raise ValueError(f"Unable to delete all media items in {object_ids}")

    def update_album(self, album_id: AlbumId, updated_album_fields: UpdatedAlbumFields):
        if album_id.client_id != self._client_id:
            raise ValueError(f"Album {album_id} belongs to a different client")

        filter_query: Mapping = {
            "_id": album_id.object_id,
        }

        set_query: Mapping = {"$set": {}}

        if updated_album_fields.new_name is not None:
            set_query["$set"]["name"] = updated_album_fields.new_name

        if updated_album_fields.new_parent_album_id is not None:
            set_query["$set"]["parent_album_id"] = album_id_to_string(
                updated_album_fields.new_parent_album_id
            )

        logger.debug(f"Updating {album_id} with new fields: {set_query}")

        session = self._mongodb_clients_repository.get_session_for_client_id(
            self._client_id,
        )
        result = self._collection.update_one(
            filter=filter_query, update=set_query, upsert=False, session=session
        )

        if result.matched_count != 1:
            raise ValueError(f"Unable to update album {album_id}")

    def update_many_albums(self, update_requests: list[UpdateAlbumRequest]):
        operations: list[pymongo.UpdateOne] = []

        for request in update_requests:
            if request.album_id.client_id != self._client_id:
                raise ValueError(
                    f"Album {request.album_id} belongs to a different client"
                )

            filter_query: Mapping = {
                "_id": request.album_id.object_id,
            }

            set_query: Mapping = {"$set": {}}

            if request.new_name is not None:
                set_query["$set"]["name"] = request.new_name

            if request.new_parent_album_id is not None:
                set_query["$set"]["parent_album_id"] = album_id_to_string(
                    request.new_parent_album_id
                )

            operation = pymongo.UpdateOne(
                filter=filter_query, update=set_query, upsert=False
            )
            operations.append(operation)

        session = self._mongodb_clients_repository.get_session_for_client_id(
            self._client_id,
        )
        result = self._collection.bulk_write(requests=operations, session=session)

        if result.matched_count != len(operations):
            raise ValueError(
                f"Unable to update all albums: {result.matched_count} "
                + f"vs {len(operations)}"
            )

    def find_child_albums(self, album_id: AlbumId) -> list[Album]:
        mongo_filter = {'parent_album_id': album_id_to_string(album_id)}

        albums = []
        session = self._mongodb_clients_repository.get_session_for_client_id(
            self._client_id,
        )
        for raw_item in self._collection.find(filter=mongo_filter, session=session):
            albums.append(
                self.__parse_raw_document_to_album_obj(self._client_id, raw_item)
            )

        return albums

    def count_child_albums(self, album_id: AlbumId) -> int:
        session = self._mongodb_clients_repository.get_session_for_client_id(
            self._client_id,
        )
        return self._collection.count_documents(
            filter={'parent_album_id': album_id_to_string(album_id)},
            session=session,
        )

    def __parse_raw_document_to_album_obj(
        self, client_id: ObjectId, raw_item: Mapping[str, Any]
    ) -> Album:
        parent_album_id = None
        if "parent_album_id" in raw_item and raw_item["parent_album_id"]:
            parent_album_id = parse_string_to_album_id(raw_item["parent_album_id"])

        return Album(
            id=AlbumId(client_id, cast(ObjectId, raw_item["_id"])),
            name=str(raw_item["name"]),
            parent_album_id=parent_album_id,
        )
