# dutch-supermarket-promotion-lakehouse

A weekly data pipeline that ingests Dutch supermarket product & promotion data, lands it in a MinIO-backed data lakehouse, and makes it queryable through Iceberg + DuckDB.

## Architecture

```
Product API  ─▶  Bronze bucket (raw JSON)  ─▶  Transform (Polars)  ─▶  Silver bucket (Iceberg table)  ─▶  Query (DuckDB)
```

- **Ingestion** — pulls products per category from the supplier API (paginated) and writes the raw JSON response straight to the `bronze` bucket in MinIO, partitioned by `year/month/week/category`.
- **Transform** — Polars cleans and normalizes the raw records: strips text fields, parses price/quantity/unit strings (pack multipliers, weights, piece counts) with regex, casts prices to `Decimal`, and adds ingestion/processing timestamps.
- **Load** — the transformed Arrow table is written to an **Iceberg** table (`silver.products`) via PyIceberg's SQL catalog, overwriting only the partition for the current category/week/year (idempotent re-runs).
- **Query** — DuckDB connects to the same MinIO/S3 storage and reads the Iceberg table with `iceberg_scan(...)` for ad-hoc analysis.
- Everything runs weekly via `runWeeklyPipeline.py`, packaged in a Docker image alongside a MinIO container (`docker-compose.yml`).

## Project structure

```
src/
├── runWeeklyPipeline.py        # entry point — orchestrates one weekly run
├── ingestion/
│   ├── getProdAPI.py           # paginated calls to the supplier product API
│   └── ingestBronzeBucket.py   # writes raw JSON per category to the bronze bucket
├── transform/
│   └── transformPolars.py      # cleans & reshapes raw JSON into the target schema
├── load/
│   └── writeSilverBucket.py    # writes/overwrites the Iceberg silver table
├── query/
│   ├── duckdbConnector.py      # DuckDB connection configured for MinIO/Iceberg
│   └── TestQuery.py            # manual script to sample the silver table
└── utils/
    ├── config.py                # loads & validates required env vars
    ├── getS3ObjectKey.py        # bronze object key naming (partitioning scheme)
    ├── getBronzeBucket.py       # reads a raw object back from the bronze bucket
    └── getTargetCats.py         # list of product categories the pipeline covers
```

## Getting started

1. Copy the environment variables below into a `.env` file in the project root.
2. Build and start the stack:
   ```bash
   docker compose up --build
   ```
   This starts a MinIO container plus the pipeline container, which runs `runWeeklyPipeline.py` once on startup.
3. To query the resulting data, run:
   ```bash
   python src/query/TestQuery.py
   ```

### Required environment variables

| Variable | Purpose |
|---|---|
| `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` | MinIO credentials |
| `MINIO_ENDPOINT` | MinIO endpoint URL (used by boto3/S3 clients) |
| `MINIO_ENDPOINT_NO_PREFIX` | MinIO endpoint without scheme (used by DuckDB's `httpfs`) |
| `MINIO_BRONZE_BUCKET` | Bucket for raw, per-category JSON |
| `MINIO_SILVER_BUCKET` | Bucket backing the Iceberg `silver.products` table |
| `MINIO_GOLD_BUCKET` | Reserved for a future aggregated/analytics layer (not yet used) |
| `SILVER_TABLE_PATH` | Path used by DuckDB to scan the silver Iceberg table |
| `PROD_API_KEY` / `PROD_API_BASE_URL` | Credentials and base URL for the upstream product API |
| `VOLUMES_PATH` | Host path mounted into the MinIO container for persistent storage |

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
- [ ] Automated tests (currently only a manual sampling script, `TestQuery.py`)
- [ ] Load the silver table straight from the PyIceberg catalog in DuckDB, instead of a manually configured `iceberg_scan` path (attempted but not yet working — see comments in `duckdbConnector.py`)
- [ ] Resolve the version-guessing / concurrent-writer edge case noted in `duckdbConnector.py`
- [ ] `.env.example` file documenting configuration for new contributors

## Notes / known limitations
- `unsafe_enable_version_guessing` is enabled in DuckDB as a workaround; it does not fully hold up when multiple writers race to update the same Iceberg table.
- The supplier API client retries pagination but does not yet back off or retry on transient failures beyond a single request.