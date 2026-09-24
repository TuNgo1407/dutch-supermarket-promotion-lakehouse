from query.duckdbConnector import connect_duckdb
from utils import config
import polars as pl

if __name__ == "__main__":
    con = connect_duckdb()
    
    result = con.sql(f"""
            SELECT * FROM  iceberg_scan('{config.SILVER_TABLE_PATH}', allow_moved_paths = true)
            LIMIT 100;
            """)
    
    result.show(max_rows=1000)
    
    print(result.pl())