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
            region_name=os.getenv("AWS_REGION", "eu-central-1"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            # locally use http://localhost:8000
            endpoint_url=os.getenv("AWS_DYNAMODB_ENDPOINT_URL", "https://dynamodb.eu-central-1.amazonaws.com")
        )

    def put_item(self, item):
        try:
            response = self.table.put_item(Item=item)
            logging.info(f"PutItem succeeded: {response}")
        except ClientError as e:
            logging.error(f"Error putting item: {e}")
