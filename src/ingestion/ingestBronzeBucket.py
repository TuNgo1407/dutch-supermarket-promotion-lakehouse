import json
import boto3
from botocore.client import Config
from botocore.client import ClientError
from ingestion.getProdAPI import get_prod_by_cats
from datetime import datetime
import time
from utils.getS3ObjectKey  import DateTuple,get_s3_object_key
from utils import config
from utils.getTargetCats import get_target_cats




def inject_weekly_bronze_to_bucket():
    run_date = datetime.now()
    
    year = run_date.strftime("%Y")
    month = run_date.strftime("%m")
    week = run_date.strftime("%V") #week number
    
    dateTuple = DateTuple(year=year,month=month,week=week)

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
        raw_json_str = get_prod_by_cats(cat).encode("utf-8")

        if not raw_json_str:
            print(f"Skipping {cat} due to fetch error.")
            continue

        object_key = get_s3_object_key(dateTuple,cat)

        s3.put_object(
            Bucket=config.MINIO_BRONZE_BUCKET,
            Key=object_key,
            Body=raw_json_str,
            ContentType = "application/json"
        )
        
        time.sleep(10)
    print(f"Landed raw data: s3://bronze/{object_key}")
    
    

