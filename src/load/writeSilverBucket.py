from pyiceberg.catalog.sql import SqlCatalog
from pyiceberg.expressions import And,EqualTo
import  os
from utils import config
from transform.transformPolars import transform
from utils.getBronzeBucket import get_bronze_bucket, DateTuple
import pyarrow as pa
from utils.getTargetCats import get_target_cats
from datetime import datetime, timezone


LAKEHOUSE_NAMESPACE = "silver"
LAKEHOUSE_PROD_TABLE = f"{LAKEHOUSE_NAMESPACE}.products"


def get_catalog():
    catalog =  SqlCatalog(
        "local_catalog",
        **{
            "uri": "sqlite:///catalog.db",
            "warehouse":"s3://silver/",
            "s3.endpoint": config.MINIO_ENDPOINT,
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
    
    
def load_to_silver_bucket(date_tuple:DateTuple):
    catalog = get_catalog()
    catalog.create_namespace_if_not_exists(LAKEHOUSE_NAMESPACE)
    
    
    if catalog.table_exists(LAKEHOUSE_PROD_TABLE):
        prd_table = catalog.load_table(LAKEHOUSE_PROD_TABLE)
    else:
        prd_table = None
        
    
    target_cats = get_target_cats()
    
    for cat in target_cats:
        arrow_table = get_prd_arrow_table(date_tuple,cat)
        
        
        if not arrow_table:
            print(f"[Loading to silver] Skipping {cat} due to fetch error.")
            continue
    
    
        if not prd_table:
            prd_table = catalog.create_table(LAKEHOUSE_PROD_TABLE,schema=arrow_table.schema)
    
        is_overwrite = And(
            EqualTo("category",cat),
            EqualTo("ingested_week",int(date_tuple.week)),
            EqualTo("ingested_year",int(date_tuple.year))
        )
        
        prd_table.overwrite(arrow_table,overwrite_filter=is_overwrite)
        print(f"Cat {cat} row written count: {arrow_table.num_rows}")
    
        



