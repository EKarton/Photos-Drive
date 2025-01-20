from collections import defaultdict
import logging
from dataclasses import dataclass
from typing import Optional, Mapping, cast, Any, Dict
from abc import ABC, abstractmethod
from bson.objectid import ObjectId
import pymongo

from .albums import Album, AlbumId
from .clients_repository import MongoDbClientsRepository
from .media_items_repository import MediaItemId

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UpdatedAlbumFields:
    new_name: Optional[str] = None
    new_parent_album_id: Optional[AlbumId] = None
    new_child_album_ids: Optional[list[AlbumId]] = None
    new_media_item_ids: Optional[list[MediaItemId]] = None


@dataclass(frozen=True)
class UpdateAlbumRequest:
    """
    Represents a request to update an existing album.

    Attributes:
        album_id (AlbumId): The ID of the album.
        new_name (Optional[str]): The new name of the album,
            if present.
        new_parent_album_id (Optional[AlbumId]): The new parent album ID,
            if present.
        new_child_album_ids (Optional[list[AlbumId]]): The new child album IDs,
            if present.
        new_media_item_ids (Optional[list[MediaItemId]]): The new media item IDs,
            if present.
    """

    album_id: AlbumId
    new_name: Optional[str] = None
    new_parent_album_id: Optional[AlbumId] = None
    new_child_album_ids: Optional[list[AlbumId]] = None
    new_media_item_ids: Optional[list[MediaItemId]] = None


class AlbumsRepository(ABC):
    """
    A class that represents a repository of albums.
    """

    @abstractmethod
    def get_album_by_id(self, id: AlbumId) -> Album:
        """
        Returns the album.

        Args:
            id (AlbumId): The album ID.

        Returns:
            Album: The album object.

        Raises:
            ValueError: If no album exists.
        """

    @abstractmethod
    def get_all_albums(self) -> list[Album]:
        '''
        Returns all of the albums in the system.

        Returns:
            list[Album]: A list of albums.
        '''

    @abstractmethod
    def create_album(
        self,
        album_name: str,
        parent_album_id: Optional[AlbumId],
        child_album_ids: list[AlbumId],
        media_item_ids: list[MediaItemId],
    ) -> Album:
        '''
        Creates an album in a MongoDB client with the most amount of space remaining

        Args:
            album_name (str): The album name
            parent_album_id (Optional[AlbumId]): The parent album ID
            child_album_ids list[AlbumId]: A list of child album IDs
            media_item_ids (list[MediaItemId]): A list of media item IDs.

        Returns:
            Album: An instance of the newly created album.
        '''

    @abstractmethod
    def delete_album(self, id: AlbumId):
        """
        Deletes a album.

        Args:
            client_id (str): The client ID.
            id (str): The album ID.

        Raises:
            ValueError: If no album exists.
        """

    @abstractmethod
    def delete_many_albums(self, ids: list[AlbumId]):
        """
        Deletes a list of albums from the database.

        Args:
            ids (list[AlbumId): The IDs of the albums to delete.

        Raises:
            ValueError: If a media item exists.
        """

    @abstractmethod
    def update_album(self, album_id: AlbumId, updated_album_fields: UpdatedAlbumFields):
        """
        Update an album with new fields.

        Args:
            album_id (AlbumId): The album ID.
            updated_album_fields (UpdatedAlbumFields): A set of updated album fields.
        """

    @abstractmethod
    def update_many_albums(self, requests: list[UpdateAlbumRequest]):
        '''
        Performs a bulk update on albums with new fields.

        Args:
            requests (list[UpdateAlbumRequest]): A list of album update requests.
        '''


class AlbumsRepositoryImpl(AlbumsRepository):
    """Implementation class for AlbumsRepository."""

    def __init__(self, mongodb_clients_repository: MongoDbClientsRepository):
        """
        Creates a AlbumsRepository

        Args:
            mongodb_clients_repository (MongoDbClientsRepository): A repo of mongo db
                clients that stores albums.
        """
        self._mongodb_clients_repository = mongodb_clients_repository

    def get_album_by_id(self, id: AlbumId) -> Album:
        client = self._mongodb_clients_repository.get_client_by_id(id.client_id)
        session = self._mongodb_clients_repository.get_session_for_client_id(
            id.client_id
        )
        raw_item = cast(
            dict,
            client["sharded_google_photos"]["albums"].find_one(
                {"_id": id.object_id}, session=session
            ),
        )

        if raw_item is None:
            raise ValueError(f"Album {id} does not exist!")

        return self.__parse_raw_document_to_album_obj(id.client_id, raw_item)

    def get_all_albums(self) -> list[Album]:
        albums: list[Album] = []
        for client_id, client in self._mongodb_clients_repository.get_all_clients():
            session = self._mongodb_clients_repository.get_session_for_client_id(
                client_id,
            )
            for doc in client["sharded_google_photos"]["albums"].find(
                filter={}, session=session
            ):
                raw_item = cast(dict, doc)
                album = self.__parse_raw_document_to_album_obj(client_id, raw_item)
                albums.append(album)

        return albums

    def create_album(
        self,
        album_name: str,
        parent_album_id: AlbumId | None,
        child_album_ids: list[AlbumId],
        media_item_ids: list[MediaItemId],
    ) -> Album:
        client_id = self._mongodb_clients_repository.find_id_of_client_with_most_space()
        client = self._mongodb_clients_repository.get_client_by_id(client_id)
        session = self._mongodb_clients_repository.get_session_for_client_id(
            client_id,
        )

        result = client["sharded_google_photos"]["albums"].insert_one(
            document={
                "name": album_name,
                "parent_album_id": (
                    f"{parent_album_id.client_id}:{parent_album_id.object_id}"
                    if parent_album_id is not None
                    else None
                ),
                "child_album_ids": [
                    f"{c_id.client_id}/{c_id.object_id}" for c_id in child_album_ids
                ],
                "media_item_ids": [
                    f"{m_id.client_id}/{m_id.object_id}" for m_id in media_item_ids
                ],
            },
            session=session,
        )

        return Album(
            id=AlbumId(client_id=client_id, object_id=result.inserted_id),
            name=album_name,
            parent_album_id=parent_album_id,
            child_album_ids=child_album_ids,
            media_item_ids=media_item_ids,
        )

    def delete_album(self, id: AlbumId):
        client = self._mongodb_clients_repository.get_client_by_id(id.client_id)
        session = self._mongodb_clients_repository.get_session_for_client_id(
            id.client_id,
        )
        result = client["sharded_google_photos"]["albums"].delete_one(
            filter={"_id": id.object_id},
            session=session,
        )

        if result.deleted_count != 1:
            raise ValueError(f"Unable to delete album: Album {id} not found")

    def delete_many_albums(self, ids: list[AlbumId]):
        client_id_to_object_ids: Dict[ObjectId, list[ObjectId]] = {}
        for id in ids:
            if id.client_id not in client_id_to_object_ids:
                client_id_to_object_ids[id.client_id] = []

            client_id_to_object_ids[id.client_id].append(id.object_id)

        for client_id, object_ids in client_id_to_object_ids.items():
            client = self._mongodb_clients_repository.get_client_by_id(client_id)
            session = self._mongodb_clients_repository.get_session_for_client_id(
                client_id,
            )
            result = client["sharded_google_photos"]["albums"].delete_many(
                filter={"_id": {"$in": object_ids}},
                session=session,
            )

            if result.deleted_count != len(object_ids):
                raise ValueError(f"Unable to delete all media items in {object_ids}")

    def update_album(self, album_id: AlbumId, updated_album_fields: UpdatedAlbumFields):
        filter_query: Mapping = {
            "_id": album_id.object_id,
        }

        set_query: Mapping = {"$set": {}}

        if updated_album_fields.new_name is not None:
            set_query["$set"]["name"] = updated_album_fields.new_name

        if updated_album_fields.new_child_album_ids is not None:
            set_query["$set"]["child_album_ids"] = [
                f"{c_id.client_id}:{c_id.object_id}"
                for c_id in updated_album_fields.new_child_album_ids
            ]

        if updated_album_fields.new_media_item_ids is not None:
            set_query["$set"]["media_item_ids"] = [
                f"{m_id.client_id}:{m_id.object_id}"
                for m_id in updated_album_fields.new_media_item_ids
            ]

        if updated_album_fields.new_parent_album_id is not None:
            c_id = updated_album_fields.new_parent_album_id.client_id
            o_id = updated_album_fields.new_parent_album_id.object_id
            set_query["$set"]["parent_album_id"] = f"{c_id}:{o_id}"

        logger.debug(f"Updating {album_id} with new fields: {set_query}")

        client = self._mongodb_clients_repository.get_client_by_id(album_id.client_id)
        session = self._mongodb_clients_repository.get_session_for_client_id(
            album_id.client_id,
        )
        result = client["sharded_google_photos"]["albums"].update_one(
            filter=filter_query, update=set_query, upsert=False, session=session
        )

        if result.matched_count != 1:
            raise ValueError(f"Unable to update album {album_id}")

    def update_many_albums(self, update_requests: list[UpdateAlbumRequest]):
        client_id_to_operations: Dict[ObjectId, list[pymongo.UpdateOne]] = defaultdict(
            list
        )

        for request in update_requests:
            filter_query: Mapping = {
                "_id": request.album_id.object_id,
            }

            set_query: Mapping = {"$set": {}}

            if request.new_name is not None:
                set_query["$set"]["name"] = request.new_name

            if request.new_child_album_ids is not None:
                set_query["$set"]["child_album_ids"] = [
                    f"{c_id.client_id}:{c_id.object_id}"
                    for c_id in request.new_child_album_ids
                ]

            if request.new_media_item_ids is not None:
                set_query["$set"]["media_item_ids"] = [
                    f"{m_id.client_id}:{m_id.object_id}"
                    for m_id in request.new_media_item_ids
                ]

            if request.new_parent_album_id is not None:
                c_id = request.new_parent_album_id.client_id
                o_id = request.new_parent_album_id.object_id
                set_query["$set"]["parent_album_id"] = f"{c_id}:{o_id}"

            operation = pymongo.UpdateOne(
                filter=filter_query, update=set_query, upsert=False
            )
            client_id_to_operations[request.album_id.client_id].append(operation)

        for client_id, operations in client_id_to_operations.items():
            client = self._mongodb_clients_repository.get_client_by_id(client_id)
            session = self._mongodb_clients_repository.get_session_for_client_id(
                client_id,
            )
            result = client["sharded_google_photos"]["albums"].bulk_write(
                requests=operations, session=session
            )

            if result.matched_count != len(operations):
                raise ValueError(
                    f"Unable to update all albums: {result.matched_count} "
                    + f"vs {len(operations)}"
                )

    def __parse_raw_document_to_album_obj(
        self, client_id: ObjectId, raw_item: Mapping[str, Any]
    ) -> Album:
        parent_album_id = None
        if "parent_album_id" in raw_item and raw_item["parent_album_id"]:
            pa_client_id, pa_object_id = raw_item["parent_album_id"].split(":")
            parent_album_id = AlbumId(ObjectId(pa_client_id), ObjectId(pa_object_id))

        child_album_ids = []
        for raw_child_album_id in raw_item["child_album_ids"]:
            ca_client_id, ca_object_id = raw_child_album_id.split(":")
            child_album_ids.append(
                AlbumId(ObjectId(ca_client_id), ObjectId(ca_object_id))
            )

        media_item_ids = []
        for raw_media_id in raw_item["media_item_ids"]:
            m_client_id, m_object_id = raw_media_id.split(":")
            media_item_ids.append(
                MediaItemId(ObjectId(m_client_id), ObjectId(m_object_id))
            )

        return Album(
            id=AlbumId(client_id, cast(ObjectId, raw_item["_id"])),
            name=str(raw_item["name"]),
            parent_album_id=parent_album_id,
            child_album_ids=child_album_ids,
            media_item_ids=media_item_ids,
        )
