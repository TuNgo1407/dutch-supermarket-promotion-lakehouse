import duckdb
from utils import config
from load.writeSilverBucket import get_catalog





def connect_duckdb():
    con = duckdb.connect()
    con.sql("INSTALL iceberg;  LOAD iceberg;")
    con.sql("INSTALL httpfs; LOAD httpfs;")
    con.sql("SET unsafe_enable_version_guessing = true;") #NOT WORK for the case: multiple writers were racing 

    con.sql(f"""
            CREATE SECRET (
                TYPE s3,
                KEY_ID '{config.MINIO_ACCESS_KEY}',
                SECRET '{config.MINIO_SECRET_KEY}',
                ENDPOINT '{config.MINIO_ENDPOINT_NO_PREFIX}',
                URL_STYLE 'path',
                USE_SSL false
            );
            """)


    return con 
    #### Not sure why this isnt working
    #catalog = get_catalog()
    #table = catalog.load_table("silver.products")
    #print(table.metadata_location)
    
    #con.sql(f"""
    #        SELECT * FROM  iceberg_scan('{TABLE_PATH}', allow_moved_paths = true)
    #        LIMIT 100;
    #        """).show()
    

