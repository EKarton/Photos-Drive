from dataclasses import dataclass
from typing import Optional, Dict, Any, cast, Mapping
from abc import ABC, abstractmethod
from bson.objectid import ObjectId

from .media_items import MediaItemId, MediaItem, GpsLocation
from .clients_repository import MongoDbClientsRepository


@dataclass(frozen=True)
class CreateMediaItemRequest:
    """
    A class that represents the parameters needed to create a new media item
    in the database.

    Attributes:
        file_name (str): The file name of the media item.
        hash_code (Optional[str]): The hash code of the media item (Optional).
        location (Optional(GpsLocation)): The location of where the media item was
            taken.
        gphotos_client_id (ObjectId): The ID of the Google Photos client that the media
            item is saved on.
        gphotos_media_item_id (str): The ID of the media item stored on Google Photos
    """

    file_name: str
    hash_code: Optional[str]
    location: Optional[GpsLocation]
    gphotos_client_id: ObjectId
    gphotos_media_item_id: str


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
            "hash_code": request.hash_code,
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
            hash_code=request.hash_code,
            location=request.location,
            gphotos_client_id=request.gphotos_client_id,
            gphotos_media_item_id=request.gphotos_media_item_id,
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

        return MediaItem(
            id=MediaItemId(client_id, cast(ObjectId, raw_item["_id"])),
            file_name=raw_item["file_name"],
            hash_code=raw_item["hash_code"],
            location=location,
            gphotos_client_id=ObjectId(raw_item["gphotos_client_id"]),
            gphotos_media_item_id=raw_item["gphotos_media_item_id"],
        )
