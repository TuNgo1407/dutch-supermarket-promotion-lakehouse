from datetime import datetime
from ingestion.ingestBronzeBucket import inject_to_bronze_bucket
from utils.getS3ObjectKey  import DateTuple
from load.writeSilverBucket import load_to_silver_bucket



def start_weekly_pipeline_lakehouse():
    run_date = datetime.now()
    year = run_date.strftime("%Y")
    month = run_date.strftime("%m")
    week = run_date.strftime("%V") #week number
    date_tuple = DateTuple(year=year,month=month,week=week)
    
    inject_to_bronze_bucket(date_tuple)
    load_to_silver_bucket(date_tuple)
    

if __name__ == "__main__":
    start_weekly_pipeline_lakehouse()