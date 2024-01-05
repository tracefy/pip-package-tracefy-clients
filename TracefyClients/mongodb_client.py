import os
from abc import ABC
from pymongo import MongoClient


class MongoDBClient(ABC):
    def __init__(self):
        username = self.get_username()
        password = self.get_password()
        host = self.get_host()
        port = self.get_port()
        auth_source = self.get_auth_source()

        mongo_uri = f"mongodb://{username}:{password}@{host}:{port}/{self.get_database_name()}?authSource={auth_source}"

        self.client = MongoClient(mongo_uri)
        self.db = self.client.get_database(
            self.get_database_name()
        )

        self.collection = self.db.get_collection(self.get_collection_name())

    def get_password(self) -> str:
        return os.getenv("MONGO_INITDB_ROOT_PASSWORD")

    def get_username(self) -> str:
        return os.getenv("MONGO_INITDB_ROOT_USERNAME")

    def get_auth_source(self) -> str:
        return os.getenv("MONGO_AUTH_SOURCE", "admin")

    def get_database_name(self) -> str:
        return os.getenv("MONGO_DB_NAME", "DB")

    def get_collection_name(self) -> str:
        return os.getenv("MONGO_DB_TABLE", "table")

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
