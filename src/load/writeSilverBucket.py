from pyiceberg.catalog.sql import SqlCatalog
from pyiceberg.expressions import And,EqualTo
import  os
from utils import config
from transform.transformPolars import transform
from utils.getBronzeBucket import get_bronze_bucket, DateTuple
import pyarrow as pa
from utils.getTargetCats import get_target_cats
from datetime import datetime, timezone

def get_catalog():
    catalog =  SqlCatalog(
        "local_catalog",
        **{
            "uri": "sqlite:///catalog.db",
            "warehouse":"s3://silver/",
            "s3.endpoint": "http://localhost:9000",
            "s3.access-key-id": config.MINIO_ACCESS_KEY,
            "s3.secret-access-key": config.MINIO_SECRET_KEY, 
            "s3.region": "us-east-1"
        }
    )
    return catalog



def get_prd_arrow_table(date_tuple:DateTuple, cat:str):
    data = get_bronze_bucket(dateTuple=date_tuple,cat=cat)
    arrow_table = transform(data)

    return arrow_table
    
    
def write_to_silver_bucket(date_tuple:DateTuple, cat:str):
    catalog = get_catalog()
    arrow_table = get_prd_arrow_table(date_tuple,cat)
    
    is_overwrite = And(
        EqualTo("category",cat),
        EqualTo("ingested_week",int(date_tuple.week)),
        EqualTo("ingested_year",int(date_tuple.year))
    )
    

    catalog.create_namespace_if_not_exists("silver")
    prd_table = catalog.create_table_if_not_exists("silver.products",schema=arrow_table.schema)
    prd_table.overwrite(arrow_table,overwrite_filter=is_overwrite)
    
        



