import polars as pl
import json
import io
from utils.getBronzeBucket import get_bronze_bucket, DateTuple
import xlsxwriter
import datetime



multiplier_regex  = r"(\d+)\s*[xx]\s*\d"  #this regex is ai-generated
measure_regex = r"(?P<value>\d+(?:[.,]\d+)?)\s*(?P<unit>kg|gr|gram|grm|g|ml|cl|liter|l)\b" #this regex is ai-generated
piece_count_regex = r"(\d+)\s*(?:stuks?|st|capsules?|zakjes?|cups?)\b"  #this regex is ai-generated



qty_clean = (
    pl.col("raw_qty").str.to_lowercase()
      .str.replace(r"\bhalve\s+kilo\b", "0.5 kg")     
      .str.replace("per stuk","1 stuks")
)

#schema-on-read
target_schema = {
    "base_product_id": pl.String,
    "name": pl.String,
    "brand": pl.String,
    "ean": pl.String,
    "price": pl.Float64,
    "original_price": pl.Float64,
    "quantity": pl.String,
    "unit": pl.String,
    "unit_price": pl.Float64,
    "product_url": pl.String,
    "image_url": pl.String,
    "retailer": pl.String,
    "unified_category": pl.String,
    "is_promotional": pl.Boolean,
    "valid_from": pl.String,   
    "valid_until": pl.String,
    "ingested_at":pl.Datetime,
    "processed_at": pl.Datetime,
}


def transform(raw_json:dict):
  if(not isinstance(raw_json,dict) or not raw_json):
    return None
  
  products = raw_json["results"]

  if(not isinstance(products,list) or not products):
    return None

  if (not isinstance(products[0],dict)):
    return None

  lf = pl.DataFrame(
    products,
    schema=target_schema,
    ).lazy()


  ingest_at = raw_json["ingest_at"]
  ingest_at_value = datetime.datetime.fromisoformat(ingest_at)
  process_at = datetime.datetime.now(datetime.timezone.utc)

  pipeline = (
    lf
    .filter(pl.col("base_product_id").is_not_null())
    .select ([
      pl.col("base_product_id").str.strip_chars(),
      pl.col("ean").str.strip_chars(),
      pl.col("name").str.strip_chars().alias("product_name"),
      pl.col("unified_category").str.strip_chars().alias("category"),
      pl.col("brand").str.strip_chars().alias("brand_name"),
      pl.col("retailer").str.strip_chars(),
      pl.col("unit").str.strip_chars(),
      pl.col("valid_from").str.to_date(format="%Y-%m-%d",strict=False).alias("valid_from"),
      pl.col("valid_until").str.to_date(format="%Y-%m-%d",strict=False).alias("valid_until"),

      "is_promotional",
      "price",
      "original_price",
      "product_url",
      "image_url",
      pl.col("quantity").cast(pl.String).alias("raw_qty"),
      "unit_price",
    ])

    .with_columns([
      pl.when(
        pl.col("original_price").is_not_null() & (pl.col("original_price") > 0)
      )
      .then (pl.col("original_price").cast(pl.Decimal(precision=7,scale=2)))
      .otherwise(None)
      .alias("original_price"),

      pl.when(
        pl.col("price").is_not_null() & (pl.col("price") > 0)
      )
      .then (pl.col("price").cast(pl.Decimal(precision=7,scale=2)))
      .otherwise(None)
      .alias("discounted_price"),

      pl.when(
        pl.col("unit_price").is_not_null() & (pl.col("unit_price") > 0)
      )
      .then (pl.col("unit_price").cast(pl.Decimal(precision=7,scale=2)))
      .otherwise(None)
      .alias("unit_price"),

      qty_clean.str.extract(multiplier_regex,1).cast(pl.Int32, strict=False).alias("pack_multiplier"),
      qty_clean.str.extract(piece_count_regex, 1).cast(pl.Int32, strict=False).alias("piece_count"),
      qty_clean.str.extract_groups(measure_regex).alias("measure_group_temp"),
      
      
      pl.lit(ingest_at_value).cast(pl.Datetime(time_zone="UTC")).alias("ingested_at"),
      pl.lit(ingest_at_value).dt.week().cast(pl.Int32).alias("ingested_week"),
      pl.lit(ingest_at_value).dt.year().cast(pl.Int32).alias("ingested_year"),
      
      pl.lit(process_at).cast(pl.Datetime).alias("process_at")
      

    ])
    .with_columns([

      pl.col("measure_group_temp")
            .struct.field("value")
            .str.replace(",", ".")
            .cast(pl.Float32, strict=False)
            .alias("qty_value"),

      pl.col("measure_group_temp")
          .struct.field("unit")
          .str.strip_chars()
          .cast(pl.String,strict=False)
          .alias("qty_unit")

    ])
    .drop("measure_group_temp","price")
  )

  pl.Config.set_tbl_cols(-1)
  arrow_df = pipeline.collect().to_arrow()

  
  return arrow_df

