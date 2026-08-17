from pathlib import Path
from typing import List
import os
import duckdb
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel
from datetime import datetime
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "weather.duckdb"

load_dotenv(PROJECT_ROOT / ".env")

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is missing from .env")

client = genai.Client(api_key=api_key)


class WeatherNarrative(BaseModel):
    city: str
    station_id: str
    observation_date: str
    narrative: str


class WeatherNarrativeBatch(BaseModel):
    narratives: List[WeatherNarrative]

def ensure_narratives_table():
    conn = duckdb.connect(str(DB_PATH))

    conn.execute("""
        create table if not exists weather_narratives (
            city varchar,
            station_id varchar,
            observation_date date,
            narrative varchar,
            model_name varchar,
            generated_at timestamp
        )
    """)

    conn.close()

def get_weather_batch(limit: int = 10):
    conn = duckdb.connect(str(DB_PATH), read_only=True)

    df = conn.execute(
        """
        select
            m.city,
            m.station_id,
            m.station_name,
            m.observation_date,
            m.tmax_c,
            m.tmin_c,
            m.tavg_c,
            m.precipitation_mm,
            m.snowfall_mm,
            m.snow_depth_mm,
            m.avg_wind_speed_ms
        from mart_daily_weather m
        left join weather_narratives n
            on m.city = n.city and m.observation_date = n.observation_date
        where n.station_id is null
        order by m.observation_date, m.city
        limit ?
        """,
        [limit],
    ).fetchdf()

    conn.close()

    # Convert dates to strings and NaN values to None
    df["observation_date"] = df["observation_date"].astype(str)
    df = df.where(df.notna(), None)

    return df.to_dict(orient="records")


def generate_narratives(records):
    prompt = f"""
Generate one concise daily weather narrative for every input record.

Use ONLY the supplied NOAA-derived measurements.

Rules:
- Do not invent weather conditions.
- Do not invent sunshine, clouds, storms, or other conditions unless the data explicitly supports them.
- Do not mention fields that are null.
- Preserve the supplied city, station_id and observation_date exactly.
- Write 2-3 sentences per record.
- Temperatures are in Celsius.
- Precipitation, snowfall, and snow depth are in millimetres.
- Wind speed is metres per second.

Input records:

{records}
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=WeatherNarrativeBatch,
            temperature=0.2,
        ),
    )

    return response.parsed

def save_narratives(result):
    rows = []

    for item in result.narratives:
        rows.append(
            {
                "city": item.city,
                "station_id": item.station_id,
                "observation_date": item.observation_date,
                "narrative": item.narrative,
                "model_name": "gemini-3.6-flash",
                "generated_at": datetime.utcnow(),
            }
        )

    df = pd.DataFrame(rows)

    conn = duckdb.connect(str(DB_PATH))

    conn.register("narratives_df", df)

    conn.execute("""
        insert into weather_narratives
        select
            city,
            station_id,
            cast(observation_date as date),
            narrative,
            model_name,
            generated_at
        from narratives_df
    """)

    conn.close()

    print(f"Saved {len(df)} narratives to DuckDB.")

def main():
    batch_size = 100
    ensure_narratives_table()

    while True:
        records = get_weather_batch(limit=batch_size)

        if not records:
            print("No new weather records to process.")
            break

        print(f"Sending {len(records)} weather records to Gemini...")

        result = generate_narratives(records)

        save_narratives(result)

        print(f"Completed batch of {len(records)} records.")

if __name__ == "__main__":
    main()