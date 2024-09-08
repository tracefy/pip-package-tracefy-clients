import os
import brotli
import base64
import boto3
import time
from mypy_boto3_sqs.service_resource import Message, Queue
from botocore.exceptions import ConnectionClosedError
from boto3.resources.base import ServiceResource
import json

from dotenv import load_dotenv

load_dotenv()


class SQSClient:
    def __init__(self, queue_name: str):
        self.sqs = boto3.resource(
            'sqs',
            endpoint_url=os.getenv("AWS_SQS_ENDPOINT_URL", "https://sqs.eu-central-1.amazonaws.com"),
            region_name=os.getenv("AWS_REGION", "eu-central-1"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )
        self.queue: Queue = self.sqs.create_queue(QueueName=queue_name, Attributes={"DelaySeconds": "5"})

    def decompress_message(self, message: Message) -> dict:
        decoded_data = base64.b64decode(message.body)
        return json.loads(brotli.decompress(decoded_data).decode("utf-8"))

    def messages_in_queue(self) -> int:
        """
        Get the amount of messages waiting in the queue
        """
        self.queue.reload()
        num_messages = self.queue.attributes["ApproximateNumberOfMessages"]
        return int(num_messages)


    def get_messages(self, retries=10, num_messages: int=1):
        """
        Get an amount of messages from the queue (default 1)
        """
        for attempt in range(retries):
            try:
                return self.queue.receive_messages(MessageAttributeNames=['All'], MaxNumberOfMessages=num_messages)
            except ConnectionClosedError:
                if attempt < retries - 1:
                    time.sleep(0.01 ** attempt) # exponenial bakcoff
                else:
                    raise

    def add_to_queue(self, data: dict|list, retries=10):
        if len(data) > 262144:
            raise ValueError(f"Message size: {len(data)} exceeds SQS limit even after compression. Consider further data reduction or splitting.")
        for attempt in range(retries):
            try:
                return self.queue.send_message(MessageBody=json.dumps(data))
            except ConnectionClosedError:
                if attempt < retries - 1:
                    time.sleep(0.01 ** attempt) # exponenial bakcoff
                else:
                    raise

    def add_compressed_to_queue(self, data: dict|list, retries=10):
        compressed = brotli.compress(json.dumps(data).encode('utf-8'))
        base_data = base64.b64encode(compressed).decode()
        if len(base_data) > 262144:
            raise ValueError(f"Message size: {len(base_data)} exceeds SQS limit even after compression. Consider further data reduction or splitting.")

        for attempt in range(retries):
            try:
                return self.queue.send_message(MessageBody=base_data)
            except ConnectionClosedError:
                if attempt < retries - 1:
                    time.sleep(0.01 ** attempt) # exponenial bakcoff
                else:
                    raise
