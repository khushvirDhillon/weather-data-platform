# Weather Data Platform

A local data platform that ingests publicly available NOAA GHCN-Daily weather data for major Canadian airport stations, transforms the data using dbt and DuckDB, performs data-quality validation, and generates AI-powered daily weather narratives using Google Gemini.

The pipeline currently covers airport weather stations for:

* Toronto
* Montreal
* Vancouver
* Calgary
* Ottawa

The solution is designed to be reproducible, metadata-driven, and extensible without requiring station-specific SQL changes.

---

## Architecture

```text
                     NOAA GHCN-Daily
                           |
          +----------------+----------------+
          |                |                |
     Observations      Stations        Inventory
     (.csv.gz)         Metadata         Metadata
          |                |                |
          +----------------+----------------+
                           |
                    Python Ingestion
                           |
                           v
                     DuckDB Raw Layer
                           |
        +------------------+------------------+
        |                                     |
 Configured Stations                 README-derived Metadata
        |                          - units / scale factors
        |                          - quality flag meanings
        +------------------+------------------+
                           |
                           v
                        dbt
                           |
             +-------------+-------------+
             |             |             |
          Staging      Intermediate      Mart
             |             |             |
             +-------------+-------------+
                           |
                           v
                  mart_daily_weather
                           |
                           v
                  Python Batch Pipeline
                           |
                           v
                     Google Gemini
                           |
                           v
                  weather_narratives
```

---

## Technology Stack

* **Python** — ingestion and LLM narrative pipeline
* **DuckDB** — local analytical database
* **dbt Core** — data transformation and testing
* **dbt-duckdb** — dbt adapter for DuckDB
* **Pandas** — ingestion and intermediate Python data handling
* **Google Gemini API** — weather narrative generation
* **Pydantic** — structured LLM response validation
* **YAML** — pipeline configuration
* **Git / GitHub** — version control and delivery

---

## Repository Structure

```text
weather-data-platform/
│
├── config/
│   └── config.yml
│
├── data/
│   └── raw/
│
├── ingestion/
│   ├── ingest.py
│   └── load_duckdb.py
│
├── narratives/
│   └── generate.py
│
├── weather_dbt/
│   ├── dbt_project.yml
│   ├── models/
│   │   ├── staging/
│   │   ├── intermediate/
│   │   └── marts/
│   └── tests/
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

Generated data, local DuckDB files, downloaded NOAA source files, and API secrets are intentionally excluded from version control.

---

# Data Sources

The project uses the NOAA Global Historical Climatology Network Daily (GHCN-Daily) dataset.

Base source:

```text
https://www.ncei.noaa.gov/pub/data/ghcn/daily/
```

The following source datasets are used:

### Daily observations

Station-level compressed CSV files from:

```text
/by_station/
```

Configured stations:

| City      | Station                       | Station ID  |
| --------- | ----------------------------- | ----------- |
| Toronto   | Toronto Pearson Intl A        | CA006158731 |
| Montreal  | Montreal Intl A (Trudeau)     | CA007025251 |
| Vancouver | Vancouver Intl A (YVR)        | CA001108395 |
| Calgary   | Calgary Intl A (YYC)          | CA003031092 |
| Ottawa    | Ottawa Macdonald-Cartier Intl | CA006106001 |

### Reference data

* `ghcnd-stations.txt`
* `ghcnd-inventory.txt`
* `ghcnd-countries.txt`
* `readme.txt`

The pipeline is currently scoped to a configurable two-year period to keep local processing and LLM generation manageable.

---

# Setup

## 1. Clone the repository

```bash
git clone <repository-url>
cd weather-data-platform
```

---

## 2. Create a Python virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

Verify dbt:

```bash
dbt --version
```

---

## 4. Configure dbt

The DuckDB dbt profile should point to the same database used by the Python ingestion pipeline.

Example `~/.dbt/profiles.yml`:

```yaml
weather_dbt:
  target: dev

  outputs:
    dev:
      type: duckdb
      path: ../data/weather.duckdb
      threads: 1
```

From the `weather_dbt` directory, verify the connection:

```bash
dbt debug
```

Expected result:

```text
All checks passed!
```

---

## 5. Configure Gemini

Create a `.env` file at the repository root:

```text
GEMINI_API_KEY=your_api_key_here
```

An example environment file can be provided as:

```text
.env.example
```

The actual `.env` file is excluded from Git.

---

# Configuration

Pipeline scope is controlled through:

```text
config/config.yml
```

Example:

```yaml
start_date: "2024-01-01"
end_date: "2025-12-31"

stations:
  - city: Toronto
    station_id: CA006158731

  - city: Montreal
    station_id: CA007025251

  - city: Vancouver
    station_id: CA001108395

  - city: Calgary
    station_id: CA003031092

  - city: Ottawa
    station_id: CA006106001
```

Station IDs are stored in configuration rather than embedded in transformation SQL.

Adding another configured station does not require changes to the dbt SQL models.

---

# Running the Pipeline

Run all commands from the repository root unless otherwise noted.

## Step 1 — Download NOAA data

```bash
python ingestion/ingest.py
```

This downloads:

* configured station observation files
* station metadata
* station inventory
* country metadata
* NOAA GHCN-Daily documentation

Existing files are not downloaded again, allowing the ingestion process to be rerun safely.

---

## Step 2 — Load DuckDB

```bash
python ingestion/load_duckdb.py
```

This creates the local DuckDB database:

```text
data/weather.duckdb
```

Raw and configuration tables include:

```text
raw_observations
raw_stations
raw_inventory
raw_countries
configured_stations
element_metadata
quality_flag_metadata
```

---

## Step 3 — Run dbt transformations

```bash
cd weather_dbt
dbt run
```

The dbt project follows three transformation layers:

```text
staging
   ↓
intermediate
   ↓
marts
```

---

## Step 4 — Run data-quality tests

```bash
dbt test
```

---

## Step 5 — Generate weather narratives

Return to the repository root:

```bash
cd ..
python narratives/generate.py
```

The narrative pipeline:

1. Reads unprocessed records from `mart_daily_weather`
2. Sends weather records to Gemini in batches
3. Requests structured JSON output
4. Validates the response structure using Pydantic
5. Writes results into `weather_narratives`
6. Repeats until all unprocessed records have been processed

The process is rerunnable. Existing `station_id + observation_date` combinations are skipped.

If all mart records have already been processed, the script exits with:

```text
No new weather records to process.
```

---

# Data Model

## Raw Layer

The raw layer preserves data close to the NOAA source.

### `raw_observations`

Contains station daily observations including:

```text
station_id
date
element
value
mflag
qflag
sflag
obs_time
```

### `raw_stations`

Station metadata including:

```text
station_id
latitude
longitude
elevation
station_name
wmo_id
```

### `raw_inventory`

Defines which weather elements are available for each station and the corresponding first and last years of unflagged data.

---

# dbt Staging Layer

Staging models standardize column names, types, and null handling while remaining close to the source.

Models include:

```text
stg_observations
stg_stations
stg_inventory
stg_configured_stations
```

Potentially invalid numeric values are handled defensively using safe casting rather than causing the entire pipeline to fail.

---

# dbt Intermediate Layer

## `int_target_stations`

Joins configured stations to NOAA station metadata.

The transformation contains no hardcoded station IDs.

```text
configured_stations
       +
stg_stations
       ↓
int_target_stations
```

---

## `int_station_elements`

Determines which elements are actually available for each configured station by joining target stations to the NOAA inventory.

```text
int_target_stations
       +
stg_inventory
       ↓
int_station_elements
```

Element selection is therefore driven by NOAA metadata rather than SQL such as:

```sql
WHERE element IN ('TMAX', 'TMIN', 'PRCP')
```

This allows different stations to expose different available measurements.

---

## `int_weather_observations`

Combines:

* target stations
* NOAA element inventory
* observations
* element metadata
* NOAA quality metadata

The model produces standardized fields including:

```text
raw_value
normalized_value
unit
quality_flag
quality_issue
is_quality_valid
```

---

# Metadata-Driven Design

A key design goal was separating **what data exists** from **how that data is interpreted**.

## Station selection

Station scope comes from:

```text
config/config.yml
```

and is exposed to dbt through:

```text
configured_stations
```

No station IDs are embedded directly in dbt SQL.

---

## Element selection

Element availability comes from:

```text
ghcnd-inventory.txt
```

The inventory provides the available weather elements and the first/last year of unflagged data for each station.

Therefore:

```text
Configuration
      ↓
Target Stations
      ↓
NOAA Inventory
      ↓
Valid Station + Element combinations
      ↓
Observations
```

Adding a station whose available elements differ from the existing stations does not require changing the element-selection SQL.

---

# NOAA Data Dictionary Usage

The downloaded NOAA `readme.txt` is used as the source definition for interpreting weather measurements and source quality metadata.

## Unit and scaling metadata

Examples include:

| Element | Meaning             | NOAA Representation | Normalized Unit |
| ------- | ------------------- | ------------------- | --------------- |
| TMAX    | Maximum temperature | tenths of °C        | °C              |
| TMIN    | Minimum temperature | tenths of °C        | °C              |
| TAVG    | Average temperature | tenths of °C        | °C              |
| PRCP    | Precipitation       | tenths of mm        | mm              |
| SNOW    | Snowfall            | mm                  | mm              |
| SNWD    | Snow depth          | mm                  | mm              |
| AWND    | Average wind speed  | tenths of m/s       | m/s             |

These definitions are represented as `element_metadata` and joined into the transformation pipeline.

As a result, unit conversion is metadata-driven instead of repeated throughout dbt SQL.

For example:

```text
raw TMAX = 253
scale factor = 0.1
normalized TMAX = 25.3 °C
```

---

## NOAA quality flags

The GHCN-Daily data dictionary defines a blank `QFLAG` as an observation that did not fail a NOAA quality-assurance check.

Examples of flagged conditions include:

| Flag | Meaning                      |
| ---- | ---------------------------- |
| D    | Duplicate check failure      |
| G    | Gap check failure            |
| I    | Internal consistency failure |
| O    | Climatological outlier       |
| S    | Spatial consistency failure  |
| T    | Temporal consistency failure |
| X    | Bounds check failure         |

These definitions are represented through `quality_flag_metadata`.

Intermediate observations expose:

```text
quality_flag
quality_issue
is_quality_valid
```

This preserves visibility into source-quality information rather than silently discarding it.

Only quality-valid observations are used in the final weather mart.

---

# Daily Weather Mart

The primary analytical mart is:

```text
mart_daily_weather
```

The mart provides one record per:

```text
station_id + observation_date
```

with measurements such as:

```text
city
station_id
station_name
observation_date
tmax_c
tmin_c
tavg_c
precipitation_mm
snowfall_mm
snow_depth_mm
avg_wind_speed_ms
```

Measurements unavailable for a particular station/date remain null.

---

# Data Quality

Data quality is assessed at multiple points in the pipeline rather than only at the final output.

## Structural validation

dbt tests validate important fields such as:

* station IDs
* dates
* city
* weather elements
* raw measurement values

Tests include:

```text
not_null
unique
```

where appropriate.

---

## Source quality

NOAA `QFLAG` values are retained and interpreted using the GHCN-Daily data dictionary.

Records that contain NOAA QA failures are identifiable through:

```text
is_quality_valid = false
```

The daily weather mart uses quality-valid observations.

---

## Domain validation

Additional checks validate weather values such as:

* reasonable temperature ranges
* non-negative precipitation
* required identifier fields

This provides multiple levels of validation:

```text
Source validation
       ↓
Structural dbt testing
       ↓
Domain validation
       ↓
Mart
```

---

# AI Weather Narratives

Daily weather narratives are generated using Google Gemini.

Input comes exclusively from:

```text
mart_daily_weather
```

The model receives structured weather measurements and is instructed to:

* use only supplied observations
* not invent missing measurements
* not infer unsupported weather conditions
* omit null measurements
* preserve station/date identifiers
* return structured JSON
* produce one concise narrative per record

Example input:

```json
{
  "city": "Calgary",
  "station_id": "CA003031092",
  "observation_date": "2025-01-15",
  "tmax_c": -8.2,
  "tmin_c": -17.4,
  "precipitation_mm": 0.0
}
```

Example narrative:

```text
Calgary had a cold day with a high of -8.2°C and a low of -17.4°C, with no recorded precipitation.
```

---

# Bulk LLM Processing

The narrative pipeline deliberately uses batches rather than making one API call per observation.

Conceptually:

```text
mart_daily_weather
       ↓
Fetch next unprocessed batch
       ↓
Gemini API
       ↓
Structured response
       ↓
weather_narratives
       ↓
Repeat
```

The current batch size is configurable in the Python script.

This reduces API overhead and satisfies the requirement to generate narratives in bulk.

---

# Idempotency

Both major Python pipelines are designed to be safely rerun.

## NOAA downloads

Existing source files are skipped rather than downloaded repeatedly.

## Narrative generation

Before selecting a mart record, the pipeline checks whether a narrative already exists for:

```text
station_id + observation_date
```

Previously processed rows are skipped.

Running the completed narrative pipeline again therefore does not generate duplicate narratives.

---

# Key Design Decisions

## DuckDB for local analytics

DuckDB provides a lightweight analytical database that requires no external infrastructure while supporting SQL and dbt effectively.

This keeps the project reproducible and appropriate for a local take-home exercise.

---

## Separate ingestion from transformation

Python handles:

* file retrieval
* fixed-width parsing
* raw loading

dbt handles:

* transformation
* business logic
* metadata joins
* quality validation
* mart construction

This provides clearer ownership between ingestion and transformation responsibilities.

---

## Preserve source data before applying business logic

The raw and staging layers retain NOAA measurements and quality metadata before transformations are applied.

This makes the pipeline easier to debug and preserves traceability back to the source.

---

## Metadata instead of station-specific SQL

Station configuration and NOAA inventory metadata drive the pipeline.

This avoids transformations that depend on the current five station IDs.

---

## Structured LLM responses

Gemini responses are constrained to a defined Pydantic schema instead of parsing free-form text.

This makes the narrative pipeline more predictable and easier to validate programmatically.

---

# Tradeoffs

## Element metadata

Unit and scaling definitions are currently represented as metadata derived from the NOAA GHCN-Daily data dictionary.

For the scope of this exercise, metadata is implemented for the weather elements relevant to the target airport stations and daily weather narratives.

A larger production implementation could parse or maintain a complete NOAA element catalog.

---

## Local database

DuckDB is ideal for the assignment's local scope but would not necessarily be the storage layer chosen for a large multi-user production platform.

A production implementation might use a cloud warehouse or lakehouse while preserving the same dbt modeling approach.

---

## LLM validation

The narrative generator constrains Gemini through structured output and prompt rules, but it does not currently perform comprehensive semantic verification of every generated statement against the underlying source values.

---

## Full-history processing

The pipeline intentionally processes a configurable recent time range rather than the entire historical station record.

This keeps processing and API usage manageable for a take-home implementation.

---

# Improvements With More Time

Given additional development time, I would prioritize:

### 1. Deterministic LLM narrative validation

Parse numerical statements from generated narratives and compare them back to `mart_daily_weather`.

This would provide an additional safeguard against unsupported LLM output.

### 2. Incremental dbt models

Convert appropriate observation and mart models to incremental processing so only newly ingested weather data is transformed.

### 3. Automated orchestration

Add local Airflow or another orchestrator to coordinate:

```text
Download
   ↓
Load
   ↓
dbt run
   ↓
dbt test
   ↓
Narrative generation
```

### 4. Broader metadata coverage

Expand element metadata to cover the complete set of GHCN-Daily elements documented by NOAA.

### 5. Stronger schema/data contracts

Add stricter dbt constraints and additional validation around:

* station metadata
* inventory date ranges
* accepted quality flags
* normalized units

### 6. Automated testing

Add Python unit tests for:

* fixed-width parsing
* configuration handling
* API response validation
* duplicate narrative prevention

### 7. CI/CD

Add GitHub Actions to automatically run:

```bash
dbt parse
dbt test
```

and Python tests on every pull request.

---

# Reproducibility

A complete rebuild can be performed with:

```bash
# Create environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download NOAA sources
python ingestion/ingest.py

# Load DuckDB
python ingestion/load_duckdb.py

# Transform and validate
cd weather_dbt
dbt run
dbt test

# Generate narratives
cd ..
python narratives/generate.py
```

---

# NOAA Dataset Citation

The project uses the Global Historical Climatology Network - Daily dataset.

Menne, M.J., I. Durre, B. Korzeniewski, S. McNeill, K. Thomas, X. Yin, S. Anthony, R. Ray, R.S. Vose, B.E. Gleason, and T.G. Houston. *Global Historical Climatology Network - Daily (GHCN-Daily), Version 3*. NOAA National Climatic Data Center.

The project also references the GHCN-Daily methodology described by Menne et al. (2012), *Journal of Atmospheric and Oceanic Technology*, 29, 897–910.

---

## Summary

This project demonstrates a local, reproducible weather data platform with:

* automated NOAA ingestion
* DuckDB-based local storage
* layered dbt transformations
* configuration-driven station selection
* metadata-driven element availability
* NOAA data-dictionary-based units and quality handling
* dbt data-quality validation
* daily weather marts
* Gemini-powered bulk narrative generation
* structured LLM output
* rerunnable, duplicate-safe processing
