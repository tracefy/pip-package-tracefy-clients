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
            aws_access_key_id=self.get_aws_secret_access_key(),
            aws_secret_access_key=self.get_aws_secret_access_key(),
            region_name=self.get_region_name()
        )
        self.s3 = session.client('s3')

    def add_to_bucket(self, key, data):
        current_date = datetime.datetime.now()
        year = current_date.year
        month = current_date.month
        day = current_date.day

        self.s3.put_object(
            Bucket=self.s3_bucket,
            Key=self.get_formatted_path(),
            Body=json.dumps(data)
        )
        print("{} : event processed".format(key))

    def get_bucket(self) -> str:
        return os.getenv("S3_BUCKET")

    def get_region_name(self) -> str:
        return os.getenv("AWS_REGION", "eu-central-1")

    def get_aws_access_key_id(self) -> str:
        return os.getenv("AWS_ACCESS_KEY_ID")

    def get_aws_secret_access_key(self) -> str:
        return os.getenv("AWS_SECRET_ACCESS_KEY")
        
    def get_formatted_path(self):
        return f"{year}/{month:02d}/{day:02d}/{key}.json"
