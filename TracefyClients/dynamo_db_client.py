import os
import logging
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()


class DynamoDBClient:
    def __init__(self):
        self.table = None
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name=self.get_aws_region(),
            aws_access_key_id=self.get_aws_access_key_id(),
            aws_secret_access_key=self.get_aws_secret_access_key(),
            # locally use http://localhost:8000
            endpoint_url=self.get_aws_dynamodb_endpoint_url()
        )

    def get_aws_access_key_id(self) -> str:
        return os.getenv("AWS_ACCESS_KEY_ID")

    def get_aws_secret_access_key(self) -> str:
        return os.getenv("AWS_SECRET_ACCESS_KEY")

    def get_aws_region(self) -> str:
        return os.getenv("AWS_REGION", "eu-central-1")

    def get_aws_dynamodb_endpoint_url(self) -> str:
        return os.getenv("AWS_DYNAMODB_ENDPOINT_URL", "https://dynamodb.eu-central-1.amazonaws.com")

    def put_item(self, item):
        try:
            response = self.table.put_item(Item=item)
            logging.info(f"PutItem succeeded: {response}")
        except ClientError as e:
            logging.error(f"Error putting item: {e}")
