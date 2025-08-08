from collections import defaultdict
from typing import Any

from bson.objectid import ObjectId
from pymongo.errors import CollectionInvalid


class MockMongoClient:
    def __init__(self):
        self.databases = defaultdict(MockDatabase)

    def __getitem__(self, db_name):
        if db_name not in self.databases:
            self.databases[db_name] = MockDatabase()
        return self.databases[db_name]

    def start_session(self):
        # Return a dummy context manager for sessions if your code uses sessions
        class DummySession:
            def __enter__(self_):
                return self_

            def __exit__(self_, exc_type, exc_value, traceback):
                pass

            def __bool__(self_):
                return False

            def start_transaction(self_):
                pass

            def commit_transaction(self_):
                pass

            def abort_transaction(self_):
                pass

            def end_session(self_):
                pass

        return DummySession()


class MockDatabase:
    def __init__(self):
        self.collections = defaultdict(lambda: MockCollection(name=None, database=self))
        self._db_stats = None

    def __getitem__(self, collection_name):
        if collection_name not in self.collections:
            self.collections[collection_name] = MockCollection(collection_name, self)
        return self.collections[collection_name]

    def command(self, cmd):
        # Provide dummy dbStats response; you can customize if you like
        if isinstance(cmd, dict) and cmd.get("dbStats") == 1:
            if self._db_stats is None:
                return {
                    "totalFreeStorageSize": 50_000_000,
                    "storageSize": 100_000,
                    "objects": sum(
                        [
                            len(self.collections[col_name]._documents)
                            for col_name in self.collections
                        ]
                    ),
                }
            return self._db_stats

        raise NotImplementedError("Only 'dbStats' commands are mocked.")

    def create_collection(self, name):
        if name not in self.collections:
            self.collections[name] = MockCollection(name, self)
            return self.collections[name]

        raise CollectionInvalid('Collection already created')

    def set_db_stats(self, new_db_stats: Any):
        self._db_stats = new_db_stats


class MockCollection:
    def __init__(self, name, database):
        self.name = name
        self.database = database
        self._documents = {}
        self._next_id = 1

    def list_search_indexes(self) -> list[str]:
        return []

    def create_search_index(self, *args, **kwargs):
        return

    def insert_many(self, documents):
        inserted_ids = []
        for doc in documents:
            _id = ObjectId()
            doc["_id"] = _id
            self._documents[_id] = doc
            inserted_ids.append(_id)

        # Return a simple object mimicking pymongo result
        class Result:
            def __init__(self, ids):
                self.inserted_ids = ids

        return Result(inserted_ids)

    def find_one(self, query):
        _id = query.get("_id")
        return self._documents.get(_id)

    def delete_many(self, query):
        ids = query.get("_id", {}).get("$in", [])
        deleted_count = 0
        for _id in ids:
            if _id in self._documents:
                del self._documents[_id]
                deleted_count += 1

        class Result:
            def __init__(self, count):
                self.deleted_count = count

        return Result(deleted_count)

    def aggregate(self, pipeline):
        # Since mongomock does not support $vectorSearch, this mock just returns all
        # docs up to limit.
        # You can improve this mock here to filter, rank or limit based on pipeline if
        # you want.
        docs = list(self._documents.values())
        limit = None
        for stage in pipeline:
            if "$vectorSearch" in stage:
                limit = stage["$vectorSearch"].get("limit")
        if limit is not None:
            docs = docs[:limit]
        return docs
