from pathlib import Path
import gzip
import csv
from datetime import datetime

import duckdb
import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DB_PATH = PROJECT_ROOT / "data" / "weather.duckdb"
CONFIG_PATH = PROJECT_ROOT / "config" / "config.yml"


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def load_observations(config):
    records = []

    start_date = datetime.strptime(
        config["start_date"], "%Y-%m-%d"
    ).date()

    end_date = datetime.strptime(
        config["end_date"], "%Y-%m-%d"
    ).date()

    for station in config["stations"]:
        station_id = station["station_id"]
        file_path = RAW_DIR / f"{station_id}.csv.gz"

        print(f"Reading {file_path.name}")

        with gzip.open(file_path, "rt") as f:
            reader = csv.reader(f)

            for row in reader:
                observation_date = datetime.strptime(
                    row[1], "%Y%m%d"
                ).date()

                if not start_date <= observation_date <= end_date:
                    continue

                records.append(
                    {
                        "station_id": row[0],
                        "date": observation_date,
                        "element": row[2],
                        "value": int(row[3]),
                        "mflag": row[4] or None,
                        "qflag": row[5] or None,
                        "sflag": row[6] or None,
                        "obs_time": row[7] or None,
                    }
                )

    return pd.DataFrame(records)


def load_stations():
    file_path = RAW_DIR / "ghcnd-stations.txt"

    rows = []

    with open(file_path, "r") as f:
        for line in f:
            rows.append(
                {
                    "station_id": line[0:11].strip(),
                    "latitude": line[12:20].strip(),
                    "longitude": line[21:30].strip(),
                    "elevation": line[31:37].strip(),
                    "state": line[38:40].strip(),
                    "station_name": line[41:71].strip(),
                    "gsn_flag": line[72:75].strip(),
                    "hcn_crn_flag": line[76:79].strip(),
                    "wmo_id": line[80:85].strip(),
                }
            )

    return pd.DataFrame(rows)


def load_inventory():
    file_path = RAW_DIR / "ghcnd-inventory.txt"

    rows = []

    with open(file_path, "r") as f:
        for line in f:
            rows.append(
                {
                    "station_id": line[0:11].strip(),
                    "latitude": line[12:20].strip(),
                    "longitude": line[21:30].strip(),
                    "element": line[31:35].strip(),
                    "first_year": line[36:40].strip(),
                    "last_year": line[41:45].strip(),
                }
            )

    return pd.DataFrame(rows)


def load_countries():
    file_path = RAW_DIR / "ghcnd-countries.txt"

    rows = []

    with open(file_path, "r") as f:
        for line in f:
            rows.append(
                {
                    "country_code": line[0:2].strip(),
                    "country_name": line[3:].strip(),
                }
            )

    return pd.DataFrame(rows)


def load_station_config(config):
    return pd.DataFrame(config["stations"])


def write_to_duckdb():
    config = load_config()

    print("Loading source files...")

    observations = load_observations(config)
    stations = load_stations()
    inventory = load_inventory()
    countries = load_countries()
    station_config = load_station_config(config)

    print("Connecting to DuckDB...")

    conn = duckdb.connect(str(DB_PATH))

    conn.register("observations_df", observations)
    conn.register("stations_df", stations)
    conn.register("inventory_df", inventory)
    conn.register("countries_df", countries)
    conn.register("station_config_df", station_config)

    conn.execute("""
        create or replace table raw_observations as
        select *
        from observations_df
    """)

    conn.execute("""
        create or replace table raw_stations as
        select *
        from stations_df
    """)

    conn.execute("""
        create or replace table raw_inventory as
        select *
        from inventory_df
    """)

    conn.execute("""
        create or replace table raw_countries as
        select *
        from countries_df
    """)

    conn.execute("""
        create or replace table configured_stations as
        select *
        from station_config_df
    """)

    print("Tables created successfully.")

    result = conn.execute("""
        select 'raw_observations' as table_name,
               count(*) as row_count
        from raw_observations

        union all

        select 'raw_stations',
               count(*)
        from raw_stations

        union all

        select 'raw_inventory',
               count(*)
        from raw_inventory

        union all

        select 'raw_countries',
               count(*)
        from raw_countries

        union all

        select 'configured_stations',
               count(*)
        from configured_stations
    """).fetchdf()

    print(result)

    conn.close()


if __name__ == "__main__":
    write_to_duckdb()