# This script does the following:
# 1. Download NOAA files
# 2. Load DuckDB
# 3. Run dbt models
# 4. Run dbt tests
# 5. Generate Gemini narratives

from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
DBT_DIR = PROJECT_ROOT / "weather_dbt"


def run_command(command, cwd=None):
    print(f"Running: {' '.join(command)}")

    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
    )

    if result.returncode != 0:
        print(f"\nPipeline failed while running: {' '.join(command)}")
        sys.exit(result.returncode)


def main():
    print("\nStarting Weather Data Platform pipeline...\n")

    # 1. Download NOAA source data
    run_command(
        [sys.executable, "ingestion/ingest.py"],
        cwd=PROJECT_ROOT,
    )

    # 2. Load raw + metadata tables into DuckDB
    run_command(
        [sys.executable, "ingestion/load_duckdb.py"],
        cwd=PROJECT_ROOT,
    )

    # 3. Run dbt transformations
    run_command(
        ["dbt", "run"],
        cwd=DBT_DIR,
    )

    # 4. Run dbt data-quality tests
    run_command(
        ["dbt", "test"],
        cwd=DBT_DIR,
    )

    # 5. Generate Gemini narratives
    run_command(
        [sys.executable, "narratives/generate.py"],
        cwd=PROJECT_ROOT,
    )

    print("Pipeline completed successfully.")


if __name__ == "__main__":
    main()