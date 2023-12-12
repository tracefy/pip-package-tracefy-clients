import os
from dotenv import load_dotenv
import redis

load_dotenv()


class RedisClient:

    def __init__(self):
        self.client = redis.StrictRedis(
            self.get_host(),
            self.get_port(),
            username=self.get_username(),
            password=self.get_password(),
            charset="utf-8",
            decode_responses=True
        )

    def get_host(self) -> str:
        return os.getenv("REDIS_DB_ADDRESS", "localhost")

    def get_port(self) -> int:
        return int(os.getenv("REDIS_DB_PORT", "6379"))

    def get_username(self) -> str:
        return os.getenv("REDIS_DB_USERNAME", "")

    def get_password(self) -> str:
        return os.getenv("REDIS_DB_PASSWORD", "")

    def get_client(self):
        return self.client
