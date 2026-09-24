import boto3
from botocore.client import Config
from utils.getS3ObjectKey import get_s3_object_key, DateTuple
import json
from utils import config



def get_bronze_bucket(dateTuple:DateTuple,cat:str):

    object_key = get_s3_object_key(dateTuple,cat)
    
    
    s3 = boto3.client(
        "s3",
        endpoint_url=config.MINIO_ENDPOINT,
        aws_access_key_id=config.MINIO_ACCESS_KEY,
        aws_secret_access_key=config.MINIO_SECRET_KEY,
        config = Config(signature_version="s3v4"),
        region_name= "us-east-1",
    )
    
    res = s3.get_object(
        Bucket=config.MINIO_BRONZE_BUCKET,
        Key = object_key,
    )
    content = res["Body"].read().decode("utf-8")
    data = json.loads(content)
    return data


