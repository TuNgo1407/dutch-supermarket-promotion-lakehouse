import os
from dotenv import load_dotenv

load_dotenv()

def get_value_env(env_var:str):
    value = os.environ.get(env_var)
    if not value:
       raise RuntimeError(f"Missing required env variable {env_var}")
    return value


SILVER_TABLE_PATH = get_value_env("SILVER_TABLE_PATH")


MINIO_ENDPOINT = get_value_env("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = get_value_env("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = get_value_env("MINIO_SECRET_KEY")

MINIO_BRONZE_BUCKET = get_value_env("MINIO_BRONZE_BUCKET")
MINIO_SILVER_BUCKET = get_value_env("MINIO_SILVER_BUCKET")
MINIO_GOLD_BUCKET = get_value_env("MINIO_GOLD_BUCKET")

PROD_API_KEY = get_value_env("PROD_API_KEY")
PROD_API_BASE_URL = get_value_env("PROD_API_BASE_URL")