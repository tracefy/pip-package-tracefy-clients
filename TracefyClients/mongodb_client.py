import os
from abc import ABC
from pymongo import MongoClient


class MongoDBClient(ABC):
    def __init__(self):
        self.client = MongoClient(
            host=self.get_host(),
            port=self.get_port()
        )
        self.db = self.client.get_database()

        self.collection = self.db.get_collection(self.get_collection_name())

    def get_collection_name(self) -> str:
        return os.getenv("MONGO_DB_TABLE", "trips")

    def get_host(self) -> str:
        return os.getenv("MONGO_DB_HOST", "localhost")

    def get_port(self) -> int:
        return int(os.getenv("MONGO_DB_PORT", "27017"))

    def get_collection(self):
        return self.collection

    def get_db(self):
        return self.db

    def get_client(self):
        return self.client

    def add_row(self, key, data):
        collection = self.db[key]
        collection.insert_one(data)
