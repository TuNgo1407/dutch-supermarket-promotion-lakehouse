import json
import boto3
from botocore.client import Config
from botocore.client import ClientError
from ingestion.getProdAPI import get_prod_by_cats
import time
from utils.getS3ObjectKey  import DateTuple,get_s3_object_key
from utils import config
from utils.getTargetCats import get_target_cats




def inject_to_bronze_bucket(dateTuple:DateTuple):


    s3 = boto3.client(
        "s3",
        endpoint_url=config.MINIO_ENDPOINT,
        aws_access_key_id=config.MINIO_ACCESS_KEY,
        aws_secret_access_key=config.MINIO_SECRET_KEY,
        config = Config(signature_version="s3v4"),
        region_name= "us-east-1",
    )
    
    target_cats = get_target_cats()
    
    for cat in target_cats:
        print(f"Fetching category: {cat}...")   
        raw_json_str = get_prod_by_cats(cat)

        if not raw_json_str:
            print(f"[Ingest to Bronze] Skipping {cat} due to fetch error.")
            continue
        
        raw_bytes = raw_json_str.encode("utf-8")

        object_key = get_s3_object_key(dateTuple,cat)

        s3.put_object(
            Bucket=config.MINIO_BRONZE_BUCKET,
            Key=object_key,
            Body=raw_bytes,
            ContentType = "application/json"
        )
        
        time.sleep(10)
    print(f"Landed raw data: s3://bronze/{object_key}")
    
    

