# dutch-supermarket-promotion-lakehouse

A weekly data pipeline that ingests Dutch supermarket product & promotion data, lands it in a MinIO-backed data lakehouse, and makes it queryable through Iceberg + DuckDB.

## Architecture

```
Product API  ─▶  [ Docker: Pipeline Container ]  ─▶  [ Docker: MinIO S3 Container ]  ─▶  Query (DuckDB)
                    ├─ Ingest (JSON)                    ├─ Bronze Bucket (raw JSON)
                    ├─ Clean (Polars)                   └─ Silver Bucket (Iceberg Table)
                    └─ Load (PyIceberg)
```

The entire infrastructure runs locally in containerized environments orchestrated via **Docker Compose**:

- **Containerized Services** — A single `docker-compose.yml` defines the local network and shared services, running an S3-compatible **MinIO** storage engine alongside the custom **pipeline container** (`weekly-pipeline`).
- **Ingestion** — pulls products per category from the supplier API and streams the raw JSON response straight to the `bronze` bucket in MinIO, partitioned by `year/month/week/category`.
- **Transform** — Polars cleans and normalizes the raw records: strips text fields, parses price/quantity/unit strings (pack multipliers, weights, piece counts) with regex, casts prices to `Decimal`, and adds ingestion/processing timestamps.
- **Load** — the transformed Arrow table is written to an **Iceberg** table (`silver.products`) via PyIceberg's SQL catalog, overwriting only the partition for the current category/week/year (idempotent re-runs).
- **Query** — DuckDB connects to the MinIO/S3 endpoint over the Docker network and reads the Iceberg table with `iceberg_scan(...)` for ad-hoc analysis.
- **Execution** — packaged into an immutable Python Docker image with locked dependencies, triggered via `runWeeklyPipeline.py` without requiring host-level runtime installations.

## Project structure

```
src/
├── runWeeklyPipeline.py        
├── ingestion/
│   ├── getProdAPI.py           
│   └── ingestBronzeBucket.py   
├── transform/
│   └── transformPolars.py      
├── load/
│   └── writeSilverBucket.py    
├── query/
│   ├── duckdbConnector.py      
│   └── TestQuery.py            
└── utils/
    ├── config.py               
    ├── getS3ObjectKey.py        
    ├── getBronzeBucket.py       
    └── getTargetCats.py         
```



## Status

### Done
- [x] Weekly ingestion from the product API, by category, into the bronze bucket (partitioned by year/month/week/category)
- [x] Cleaning & transformation with Polars (price/quantity/unit parsing, schema normalization, decimal casting)
- [x] Silver layer as an Iceberg table (PyIceberg SQL catalog), with per-category/week overwrite so re-runs are idempotent
- [x] Ad-hoc querying via DuckDB (`iceberg_scan` over MinIO/S3)
- [x] Dockerized pipeline + MinIO, runnable with a single `docker compose up`

### To do / future work
- [ ] **Orchestration with Dagster** — replace the single-script weekly run with scheduled, observable, retry-aware jobs
- [ ] **Analytics / gold layer** — build aggregated tables and reporting on top of `silver.products` (the `MINIO_GOLD_BUCKET` variable is reserved for this but unused so far)


