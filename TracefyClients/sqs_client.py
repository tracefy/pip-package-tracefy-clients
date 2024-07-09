import os
import brotli
import base64
import boto3
import time
from botocore.exceptions import ConnectionClosedError
import json

from dotenv import load_dotenv

load_dotenv()


class SQSClient:
    def __init__(self):
        self.sqs = boto3.resource(
            'sqs',
            endpoint_url=self.get_endpoint_url(),
            region_name=self.get_region_name(),
            aws_access_key_id=self.get_aws_access_key_id(),
            aws_secret_access_key=self.get_aws_secret_access_key()
        )

    def get_endpoint_url(self) -> str:
        return os.getenv("AWS_SQS_ENDPOINT_URL", "https://sqs.eu-central-1.amazonaws.com")

    def get_region_name(self) -> str:
        return os.getenv("AWS_REGION", "eu-central-1")

    def get_aws_access_key_id(self) -> str:
        return os.getenv("AWS_ACCESS_KEY_ID")

    def get_aws_secret_access_key(self) -> str:
        return os.getenv("AWS_SECRET_ACCESS_KEY")

    def get_compressed_message(self, queue):
        messages = self.get_messages(queue)
        if not messages:
            return []

        decoded_messages = []
        for message in messages:
            decoded_data = base64.b64decode(message.body)
            decoded_messages.append(json.loads(brotli.decompress(decoded_data).decode("utf-8")))
        return decoded_messages


    def get_messages(self, queue, retries=10):
        for attempt in range(retries):
            try:
                return queue.receive_messages(MessageAttributeNames=['All'])
            except ConnectionClosedError:
                if attempt < retries - 1:
                    time.sleep(0.01 ** attempt) # exponenial bakcoff
                else:
                    raise

    def add_to_queue(self, queue, data: dict|list, retries=10):
        if len(data) > 262144:
            raise ValueError(f"Message size: {len(data)} exceeds SQS limit even after compression. Consider further data reduction or splitting.")
        for attempt in range(retries):
            try:
                return queue.send_message(MessageBody=json.dumps(data))
            except ConnectionClosedError:
                if attempt < retries - 1:
                    time.sleep(0.01 ** attempt) # exponenial bakcoff
                else:
                    raise

    def add_compressed_to_queue(self, queue, data: dict|list, retries=10):
        compressed = brotli.compress(json.dumps(data).encode('utf-8'))
        base_data = base64.b64encode(compressed).decode()
        if len(base_data) > 262144:
            raise ValueError(f"Message size: {len(base_data)} exceeds SQS limit even after compression. Consider further data reduction or splitting.")

        for attempt in range(retries):
            try:
                return queue.send_message(MessageBody=base_data)
            except ConnectionClosedError:
                if attempt < retries - 1:
                    time.sleep(0.01 ** attempt) # exponenial bakcoff
                else:
                    raise
