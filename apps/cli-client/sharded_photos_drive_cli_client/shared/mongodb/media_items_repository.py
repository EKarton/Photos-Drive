from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, cast, Mapping
from abc import ABC, abstractmethod
from bson import Binary
from bson.objectid import ObjectId
import pymongo

from .media_item_id import MediaItemId
from .album_id import AlbumId, parse_string_to_album_id
from .album_id import album_id_to_string
from .media_items import MediaItem, GpsLocation
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
        gphotos_media_item_id (str): The ID of the media item stored on Google Photos.
        album_id (AlbumId): The album that this media item belongs to.
        width (int): The width of the media item.
        height (int): The height of the media item.
        new_date_taken (datetime): The date and time of when the media item was taken.
    """

    file_name: str
    file_hash: bytes
    location: Optional[GpsLocation]
    gphotos_client_id: ObjectId
    gphotos_media_item_id: str
    album_id: AlbumId
    width: int
    height: int
    date_taken: datetime


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
        new_album_id (Optional[AlbumId]): The new Album ID.
        new_width (Optional[int]): The new width.
        new_height (Optional[int]): The new height.
        new_date_taken (Optional[datetime]): The new date and time of when the
            image / video was taken.
    '''

    media_item_id: MediaItemId
    new_file_name: Optional[str] = None
    new_file_hash: Optional[bytes] = None
    clear_location: Optional[bool] = False
    new_location: Optional[GpsLocation] = None
    new_gphotos_client_id: Optional[ObjectId] = None
    new_gphotos_media_item_id: Optional[str] = None
    new_album_id: Optional[AlbumId] = None
    new_width: Optional[int] = None
    new_height: Optional[int] = None
    new_date_taken: Optional[datetime] = None


@dataclass(frozen=True)
class FindMediaItemRequest:
    '''
    A class that represents the parameters needed to find existing media items in
    the database.

    Attributes:
        mongodb_client_ids (Optional[list[ObjectId]): A list of client IDs to search
            through, if present. If not present, it will search through all MongoDB
            clients.
        file_name (Optional[str]): The file name, if present.
        album_id (Optional[AlbumId]): The Album ID, if present.
    '''

    mongodb_client_ids: Optional[list[ObjectId]] = None
    file_name: Optional[str] = None
    album_id: Optional[AlbumId] = None


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
    def find_media_items(self, request: FindMediaItemRequest) -> list[MediaItem]:
        '''
        Finds all media items that satisfies the request.

        Args:
            request (FindMediaItemRequest): The request.

        Returns:
            list[MediaItem]: A list of found media items.
        '''

    @abstractmethod
    def get_num_media_items_in_album(self, album_id: AlbumId) -> int:
        '''
        Returns the total number of media items in an album.

        Args:
            album_id (AlbumId): The album ID.

        Returns:
            int: total number of media items in an album.
        '''

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

    def find_media_items(self, request: FindMediaItemRequest) -> list[MediaItem]:
        all_clients = self._mongodb_clients_repository.get_all_clients()
        if request.mongodb_client_ids is not None:
            clients = [
                (client_id, client)
                for client_id, client in all_clients
                if client_id in request.mongodb_client_ids
            ]
        else:
            clients = all_clients

        mongo_filter = {}
        if request.album_id:
            mongo_filter['album_id'] = album_id_to_string(request.album_id)
        if request.file_name:
            mongo_filter['file_name'] = request.file_name

        media_items = []
        for client_id, client in clients:
            session = self._mongodb_clients_repository.get_session_for_client_id(
                client_id,
            )
            for raw_item in client['sharded_google_photos']['media_items'].find(
                filter=mongo_filter, session=session
            ):
                media_items.append(
                    self.__parse_raw_document_to_media_item_obj(client_id, raw_item)
                )

        return media_items

    def get_num_media_items_in_album(self, album_id: AlbumId) -> int:
        total = 0
        for client_id, client in self._mongodb_clients_repository.get_all_clients():
            session = self._mongodb_clients_repository.get_session_for_client_id(
                client_id,
            )
            total += client['sharded_google_photos']['media_items'].count_documents(
                filter={'album_id': album_id_to_string(album_id)}, session=session
            )

        return total

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
            "album_id": album_id_to_string(request.album_id),
            "width": request.width,
            "height": request.height,
            "date_taken": request.date_taken,
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
            album_id=request.album_id,
            width=request.width,
            height=request.height,
            date_taken=request.date_taken,
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
            if request.new_album_id is not None:
                set_query["$set"]['album_id'] = album_id_to_string(request.new_album_id)
            if request.new_width is not None:
                set_query['$set']['width'] = request.new_width
            if request.new_height is not None:
                set_query['$set']['height'] = request.new_height
            if request.new_date_taken is not None:
                set_query['$set']['date_taken'] = request.new_date_taken

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

        width = 0
        if 'width' in raw_item and raw_item['width']:
            width = raw_item['width']

        height = 0
        if 'height' in raw_item and raw_item['height']:
            height = raw_item['height']

        date_taken = None
        if 'date_taken' in raw_item and raw_item['date_taken']:
            date_taken = cast(datetime, raw_item['date_taken'])
        else:
            date_taken = datetime(1970, 1, 1)

        return MediaItem(
            id=MediaItemId(client_id, cast(ObjectId, raw_item["_id"])),
            file_name=raw_item["file_name"],
            file_hash=file_hash,
            location=location,
            gphotos_client_id=ObjectId(raw_item["gphotos_client_id"]),
            gphotos_media_item_id=raw_item["gphotos_media_item_id"],
            album_id=parse_string_to_album_id(raw_item['album_id']),
            width=width,
            height=height,
            date_taken=date_taken,
        )
