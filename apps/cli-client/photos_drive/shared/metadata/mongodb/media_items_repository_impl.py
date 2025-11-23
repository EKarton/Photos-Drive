from collections import defaultdict
from datetime import datetime
import logging
from typing import Any, Dict, Mapping, cast

from bson import Binary
from bson.objectid import ObjectId
import pymongo

from photos_drive.shared.llm.vector_stores.base_vector_store import (
    embedding_id_to_string,
    parse_string_to_embedding_id,
)
from photos_drive.shared.metadata.album_id import (
    AlbumId,
    album_id_to_string,
    parse_string_to_album_id,
)
from photos_drive.shared.metadata.gps_location import GpsLocation
from photos_drive.shared.metadata.media_item_id import MediaItemId
from photos_drive.shared.metadata.media_items import (
    MediaItem,
)
from photos_drive.shared.metadata.media_items_repository import (
    CreateMediaItemRequest,
    FindMediaItemRequest,
    MediaItemsRepository,
    UpdateMediaItemRequest,
)
from photos_drive.shared.metadata.mongodb.clients_repository_impl import (
    MongoDbClientsRepository,
)

logger = logging.getLogger(__name__)

LOCATION_INDEX_NAME = 'location_index'


class MediaItemsRepositoryImpl(MediaItemsRepository):
    """Implementation class for MediaItemsRepository."""

    def __init__(
        self,
        mongodb_clients_repository: MongoDbClientsRepository,
        location_index_name=LOCATION_INDEX_NAME,
    ):
        """
        Creates a MediaItemsRepository

        Args:
            mongodb_clients_repository (MongoDbClientsRepository): A repo of mongo db
                clients that stores albums.
        """
        self._mongodb_clients_repository = mongodb_clients_repository

        for _, client in self._mongodb_clients_repository.get_all_clients():
            collection = client["photos_drive"]["media_items"]
            if not self.__has_location_index(collection, location_index_name):
                self.__create_location_index(collection, location_index_name)

    def __has_location_index(self, collection, index_name):
        return any(
            [index["name"] == index_name for index in collection.list_search_indexes()]
        )

    def __create_location_index(self, collection, index_name):
        collection.create_index([("location", "2dsphere")], name=index_name)
        logger.debug(f'Created location index {index_name}')

    def get_media_item_by_id(self, id: MediaItemId) -> MediaItem:
        client = self._mongodb_clients_repository.get_client_by_id(id.client_id)
        session = self._mongodb_clients_repository.get_session_for_client_id(
            id.client_id,
        )
        raw_item = cast(
            dict,
            client["photos_drive"]["media_items"].find_one(
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
            for doc in client["photos_drive"]["media_items"].find(
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

        mongo_filter: dict[str, Any] = {}
        if request.album_id:
            mongo_filter['album_id'] = album_id_to_string(request.album_id)
        if request.file_name:
            mongo_filter['file_name'] = request.file_name

        if request.earliest_date_taken or request.latest_date_taken:
            date_taken_query = {}
            if request.earliest_date_taken:
                date_taken_query['$gte'] = request.earliest_date_taken
            if request.latest_date_taken:
                date_taken_query["$lte"] = request.latest_date_taken
            mongo_filter["date_taken"] = date_taken_query

        if request.location_range:
            mongo_filter['location'] = {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [
                            request.location_range.location.longitude,
                            request.location_range.location.latitude,
                        ],
                    },
                    "$maxDistance": request.location_range.radius,
                }
            }

        media_items = []
        for client_id, client in clients:
            session = self._mongodb_clients_repository.get_session_for_client_id(
                client_id,
            )
            query = client['photos_drive']['media_items'].find(
                filter=mongo_filter, session=session
            )
            if request.limit:
                query = query.limit(request.limit)

            for raw_item in query:
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
            total += client['photos_drive']['media_items'].count_documents(
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

        if request.embedding_id:
            data_object["embedding_id"] = embedding_id_to_string(request.embedding_id)

        insert_result = client["photos_drive"]["media_items"].insert_one(
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
            embedding_id=request.embedding_id,
        )

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

            if request.clear_embedding_id:
                set_query["$set"]['embedding_id'] = None
            elif request.new_embedding_id is not None:
                set_query["$set"]['embedding_id'] = embedding_id_to_string(
                    request.new_embedding_id
                )

            operation = pymongo.UpdateOne(
                filter=filter_query, update=set_query, upsert=False
            )
            client_id_to_operations[request.media_item_id.client_id].append(operation)

        for client_id, operations in client_id_to_operations.items():
            client = self._mongodb_clients_repository.get_client_by_id(client_id)
            session = self._mongodb_clients_repository.get_session_for_client_id(
                client_id,
            )
            result = client["photos_drive"]["media_items"].bulk_write(
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
        result = client["photos_drive"]["media_items"].delete_one(
            {"_id": id.object_id}, session=session
        )

        if result.deleted_count != 1:
            raise ValueError(f"Unable to delete media item: {id} not found")

    def delete_many_media_items(self, ids: list[MediaItemId]):
        if len(ids) == 0:
            return

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
            result = client["photos_drive"]["media_items"].delete_many(
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

        date_taken = None
        if 'date_taken' in raw_item and raw_item['date_taken']:
            date_taken = cast(datetime, raw_item['date_taken'])
        else:
            date_taken = datetime(1970, 1, 1)

        width = 0
        if 'width' in raw_item and raw_item['width']:
            width = cast(int, raw_item['width'])

        height = 0
        if 'height' in raw_item and raw_item['height']:
            height = cast(int, raw_item['height'])

        embedding_id = None
        if "embedding_id" in raw_item and raw_item["embedding_id"]:
            embedding_id = parse_string_to_embedding_id(raw_item["embedding_id"])

        return MediaItem(
            id=MediaItemId(client_id, cast(ObjectId, raw_item["_id"])),
            file_name=raw_item["file_name"],
            file_hash=bytes(raw_item["file_hash"]),
            location=location,
            gphotos_client_id=ObjectId(raw_item["gphotos_client_id"]),
            gphotos_media_item_id=raw_item["gphotos_media_item_id"],
            album_id=parse_string_to_album_id(raw_item['album_id']),
            width=width,
            height=height,
            date_taken=date_taken,
            embedding_id=embedding_id,
        )
