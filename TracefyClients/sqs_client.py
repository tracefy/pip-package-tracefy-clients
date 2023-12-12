import os
import boto3
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
        return os.getenv("AWS_SQS_ENDPOINT_URL", "sqs.eu-central-1.amazonaws.com")

    def get_region_name(self) -> str:
        return os.getenv("AWS_REGION", "eu-central-1")

    def get_aws_access_key_id(self) -> str:
        return os.getenv("AWS_ACCESS_KEY_ID")

    def get_aws_secret_access_key(self) -> str:
        return os.getenv("AWS_SECRET_ACCESS_KEY")
