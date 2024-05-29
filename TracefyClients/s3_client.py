import datetime
import json
import os
import boto3
from dotenv import load_dotenv

load_dotenv()


class S3Client:
    def __init__(self):
        self.s3_bucket = self.get_bucket()
        session = boto3.Session(
            aws_access_key_id=self.get_aws_access_key_id(),
            aws_secret_access_key=self.get_aws_secret_access_key(),
            region_name=self.get_region_name()
        )
        self.s3 = session.client('s3')

    def _add_to_bucket(self, key, data, prefix: str = ""):
        current_date = datetime.datetime.now()
        year = current_date.year
        month = current_date.month
        day = current_date.day
        formatted_path = prefix + self.get_formatted_path(year, month, day, key)

        self.s3.put_object(
            Bucket=self.s3_bucket,
            Key=formatted_path,
            Body=json.dumps(data)
        )
        print("{} : row processed".format(key))

    def add_to_bucket(self, key, data):
        self._add_to_bucket(
            key=key,
            data=data
        )

    def add_to_bucket_with_prefix(self, key, data, perfix: str):
        self._add_to_bucket(
            key=key,
            data=data,
            prefix=perfix
        )

    def get_formatted_path(self, year, month, day, key):
        return f"{year}/{month:02d}/{day:02d}/{key}.json"

    def get_bucket(self) -> str:
        return os.getenv("S3_BUCKET")

    def get_region_name(self) -> str:
        return os.getenv("AWS_REGION", "eu-central-1")

    def get_aws_access_key_id(self) -> str:
        return os.getenv("AWS_ACCESS_KEY_ID")

    def get_aws_secret_access_key(self) -> str:
        return os.getenv("AWS_SECRET_ACCESS_KEY")
