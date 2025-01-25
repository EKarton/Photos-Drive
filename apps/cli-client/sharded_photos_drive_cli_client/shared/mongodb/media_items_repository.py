from collections import defaultdict
from dataclasses import dataclass
from typing import Optional, Dict, Any, cast, Mapping
from abc import ABC, abstractmethod
from bson import Binary
from bson.objectid import ObjectId
import pymongo

from .media_items import MediaItemId, MediaItem, GpsLocation
from .clients_repository import MongoDbClientsRepository


@dataclass(frozen=True)
class CreateMediaItemRequest:
    """
    A class that represents the parameters needed to create a new media item
    in the database.

    Attributes:
        file_name (str): The file name of the media item.
        file_hash (bytes): The hash of the media item, in bytes.
        location (Optional(GpsLocation)): The location of where the media item was
            taken.
        gphotos_client_id (ObjectId): The ID of the Google Photos client that the media
            item is saved on.
        gphotos_media_item_id (str): The ID of the media item stored on Google Photos
    """

    file_name: str
    file_hash: bytes
    location: Optional[GpsLocation]
    gphotos_client_id: ObjectId
    gphotos_media_item_id: str


@dataclass(frozen=True)
class UpdateMediaItemRequest:
    '''
    A class that represents the parameters needed to update an existing media item in
    the database.

    Attributes:
        media_item_id (MediaItemId): The ID of the media item to update.
        new_file_name (Optional[str]): The new file name, if present.
        new_file_hash (Optional[bytes]): The new file hash, if present.
        clear_location (Optional[bool]): Whether to clear the gps location or not,
            if present.
        new_location (Optional[GpsLocation | None]): The new gps location,
            if present.
        new_gphotos_client_id (Optional[ObjectId]): The new GPhotos client ID,
            if present.
        new_gphotos_media_item_id (Optional[str]): The new GPhotos media item ID,
            if present.
    '''

    media_item_id: MediaItemId
    new_file_name: Optional[str] = None
    new_file_hash: Optional[bytes] = None
    clear_location: Optional[bool] = False
    new_location: Optional[GpsLocation] = None
    new_gphotos_client_id: Optional[ObjectId] = None
    new_gphotos_media_item_id: Optional[str] = None


class MediaItemsRepository(ABC):
    """
    A class that represents a repository of all of the media items in the database.
    """

    @abstractmethod
    def get_media_item_by_id(self, id: MediaItemId) -> MediaItem:
        """
        Returns the media item by ID.

        Args:
            id (MediaItemId): The media item id

        Returns:
            MediaItem: The media item
        """

    @abstractmethod
    def get_all_media_items(self) -> list[MediaItem]:
        """
        Returns all media items.

        Returns:
            list[MediaItem]: A list of all media items.
        """

    @abstractmethod
    def create_media_item(self, request: CreateMediaItemRequest) -> MediaItem:
        """
        Creates a new media item in the database.

        Args:
            request (CreateMediaItemRequest): The request to create media item.

        Returns:
            MediaItem: The media item.
        """

    @abstractmethod
    def update_media_item(self, request: UpdateMediaItemRequest):
        '''
        Updates a media item in the database.

        Args:
            requests (UpdateMediaItemRequest): A request to update a media item.
        '''

    @abstractmethod
    def update_many_media_items(self, requests: list[UpdateMediaItemRequest]):
        '''
        Updates many media items in the database.

        Args:
            requests (list[UpdateMediaItemRequest]):
                A list of requests to update many media item.
        '''

    @abstractmethod
    def delete_media_item(self, id: MediaItemId):
        """
        Deletes a media item from the database.

        Args:
            id (MediaItemId): The ID of the media item to delete.

        Raises:
            ValueError: If no media item exists.
        """

    @abstractmethod
    def delete_many_media_items(self, ids: list[MediaItemId]):
        """
        Deletes a list of media items from the database.

        Args:
            ids (list[MediaItemId): The IDs of the media items to delete.

        Raises:
            ValueError: If a media item exists.
        """


class MediaItemsRepositoryImpl(MediaItemsRepository):
    """Implementation class for MediaItemsRepository."""

    def __init__(self, mongodb_clients_repository: MongoDbClientsRepository):
        """
        Creates a MediaItemsRepository

        Args:
            mongodb_clients_repository (MongoDbClientsRepository): A repo of mongo db
                clients that stores albums.
        """
        self._mongodb_clients_repository = mongodb_clients_repository

    def get_media_item_by_id(self, id: MediaItemId) -> MediaItem:
        client = self._mongodb_clients_repository.get_client_by_id(id.client_id)
        session = self._mongodb_clients_repository.get_session_for_client_id(
            id.client_id,
        )
        raw_item = cast(
            dict,
            client["sharded_google_photos"]["media_items"].find_one(
                filter={"_id": id.object_id}, session=session
            ),
        )
        if raw_item is None:
            raise ValueError(f"Media item {id} does not exist!")

        return self.__parse_raw_document_to_media_item_obj(id.client_id, raw_item)

    def get_all_media_items(self) -> list[MediaItem]:
        media_items: list[MediaItem] = []

        for client_id, client in self._mongodb_clients_repository.get_all_clients():
            session = self._mongodb_clients_repository.get_session_for_client_id(
                client_id,
            )
            for doc in client["sharded_google_photos"]["media_items"].find(
                filter={}, session=session
            ):
                raw_item = cast(dict, doc)
                media_item = self.__parse_raw_document_to_media_item_obj(
                    client_id, raw_item
                )
                media_items.append(media_item)

        return media_items

    def create_media_item(self, request: CreateMediaItemRequest) -> MediaItem:
        client_id = self._mongodb_clients_repository.find_id_of_client_with_most_space()
        client = self._mongodb_clients_repository.get_client_by_id(client_id)
        session = self._mongodb_clients_repository.get_session_for_client_id(
            client_id,
        )

        data_object: Any = {
            "file_name": request.file_name,
            'file_hash': Binary(request.file_hash),
            "gphotos_client_id": str(request.gphotos_client_id),
            "gphotos_media_item_id": str(request.gphotos_media_item_id),
        }

        if request.location:
            data_object["location"] = {
                "type": "Point",
                "coordinates": [request.location.longitude, request.location.latitude],
            }

        insert_result = client["sharded_google_photos"]["media_items"].insert_one(
            document=data_object, session=session
        )

        return MediaItem(
            id=MediaItemId(client_id=client_id, object_id=insert_result.inserted_id),
            file_name=request.file_name,
            file_hash=request.file_hash,
            location=request.location,
            gphotos_client_id=request.gphotos_client_id,
            gphotos_media_item_id=request.gphotos_media_item_id,
        )

    def update_media_item(self, request: UpdateMediaItemRequest):
        self.update_many_media_items([request])

    def update_many_media_items(self, requests: list[UpdateMediaItemRequest]):
        client_id_to_operations: Dict[ObjectId, list[pymongo.UpdateOne]] = defaultdict(
            list
        )
        for request in requests:
            filter_query: Mapping = {
                "_id": request.media_item_id.object_id,
            }

            set_query: Mapping = {"$set": {}, "$unset": {}}

            if request.new_file_name is not None:
                set_query["$set"]["file_name"] = request.new_file_name
            if request.new_file_hash is not None:
                set_query["$set"]["file_hash"] = Binary(request.new_file_hash)
                set_query["$unset"]["hash_code"] = 1
            if request.new_gphotos_client_id is not None:
                set_query["$set"]['gphotos_client_id'] = str(
                    request.new_gphotos_client_id
                )
            if request.new_gphotos_media_item_id is not None:
                set_query["$set"]['gphotos_media_item_id'] = str(
                    request.new_gphotos_media_item_id
                )

            if request.clear_location:
                set_query["$set"]['location'] = None
            elif request.new_location is not None:
                set_query["$set"]['location'] = {
                    "type": "Point",
                    "coordinates": [
                        request.new_location.longitude,
                        request.new_location.latitude,
                    ],
                }

            operation = pymongo.UpdateOne(
                filter=filter_query, update=set_query, upsert=False
            )
            client_id_to_operations[request.media_item_id.client_id].append(operation)

        for client_id, operations in client_id_to_operations.items():
            client = self._mongodb_clients_repository.get_client_by_id(client_id)
            session = self._mongodb_clients_repository.get_session_for_client_id(
                client_id,
            )
            result = client["sharded_google_photos"]["media_items"].bulk_write(
                requests=operations, session=session
            )

            if result.matched_count != len(operations):
                raise ValueError(
                    f"Unable to update all media items: {result.matched_count} "
                    + f"vs {len(operations)}"
                )

    def delete_media_item(self, id: MediaItemId):
        client = self._mongodb_clients_repository.get_client_by_id(id.client_id)
        session = self._mongodb_clients_repository.get_session_for_client_id(
            id.client_id
        )
        result = client["sharded_google_photos"]["media_items"].delete_one(
            {"_id": id.object_id}, session=session
        )

        if result.deleted_count != 1:
            raise ValueError(f"Unable to delete media item: {id} not found")

    def delete_many_media_items(self, ids: list[MediaItemId]):
        client_id_to_object_ids: Dict[ObjectId, list[ObjectId]] = {}
        for id in ids:
            if id.client_id not in client_id_to_object_ids:
                client_id_to_object_ids[id.client_id] = []

            client_id_to_object_ids[id.client_id].append(id.object_id)

        for client_id, object_ids in client_id_to_object_ids.items():
            client = self._mongodb_clients_repository.get_client_by_id(client_id)
            session = self._mongodb_clients_repository.get_session_for_client_id(
                client_id
            )
            result = client["sharded_google_photos"]["media_items"].delete_many(
                filter={"_id": {"$in": object_ids}}, session=session
            )

            if result.deleted_count != len(object_ids):
                raise ValueError(f"Unable to delete all media items in {object_ids}")

    def __parse_raw_document_to_media_item_obj(
        self, client_id: ObjectId, raw_item: Mapping[str, Any]
    ) -> MediaItem:
        location: GpsLocation | None = None
        if "location" in raw_item and raw_item["location"]:
            location = GpsLocation(
                longitude=float(raw_item["location"]["coordinates"][0]),
                latitude=float(raw_item["location"]["coordinates"][1]),
            )

        file_hash = None
        if 'file_hash' in raw_item and raw_item['file_hash']:
            file_hash = bytes(raw_item["file_hash"])
        else:
            file_hash = b''

        return MediaItem(
            id=MediaItemId(client_id, cast(ObjectId, raw_item["_id"])),
            file_name=raw_item["file_name"],
            file_hash=file_hash,
            location=location,
            gphotos_client_id=ObjectId(raw_item["gphotos_client_id"]),
            gphotos_media_item_id=raw_item["gphotos_media_item_id"],
        )
