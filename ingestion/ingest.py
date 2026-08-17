from pathlib import Path
import requests
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CONFIG_PATH = PROJECT_ROOT / "config" / "config.yml"

RAW_DIR.mkdir(parents=True, exist_ok=True)

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def download_file(url: str, destination: Path):
    if destination.exists():
        print(f"Already exists: {destination.name}")
        return

    print(f"Downloading: {destination.name}")

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    destination.write_bytes(response.content)


def main():
    config = load_config()
    base_url = config["base_url"]
    # Download station observation files
    for station in config["stations"]:
        station_id = station["station_id"]
        filename = f"{station_id}.csv.gz"

        url = f"{base_url}/by_station/{filename}"
        destination = RAW_DIR / filename

        download_file(url, destination)

    # Download metadata/reference files
    metadata_files = [
        "ghcnd-stations.txt",
        "ghcnd-inventory.txt",
        "ghcnd-countries.txt",
        "readme.txt",
    ]

    for filename in metadata_files:
        url = f"{base_url}/{filename}"
        destination = RAW_DIR / filename

        download_file(url, destination)


if __name__ == "__main__":
    main()