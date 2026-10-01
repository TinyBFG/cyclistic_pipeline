from pathlib import Path

import pandas as pd

from src.analyze_data import summarize_by_member_type
from src.clean_data import clean_trip_data
from src.load_data import find_csv_files, load_trip_data, load_trip_files


def test_combining_multiple_csv_files():
    sample_folder = Path(__file__).resolve().parents[1] / "data" / "sample"

    result = load_trip_data(sample_folder)

    assert len(result) == 5
    assert set(result["ride_id"]) == {"ride_1", "ride_2", "ride_3", "ride_4", "ride_5"}


def test_loading_discovered_csv_files():
    sample_folder = Path(__file__).resolve().parents[1] / "data" / "sample"
    csv_files = find_csv_files(sample_folder)

    result = load_trip_files(csv_files)

    assert len(csv_files) == 2
    assert len(result) == 5


def test_summary_calculations_by_member_type():
    data = pd.DataFrame(
        {
            "ride_id": ["ride_1", "ride_2", "ride_3"],
            "rideable_type": ["classic_bike", "electric_bike", "classic_bike"],
            "started_at": [
                "2023-01-01 10:00:00",
                "2023-01-01 11:00:00",
                "2023-01-01 12:00:00",
            ],
            "ended_at": [
                "2023-01-01 10:20:00",
                "2023-01-01 11:40:00",
                "2023-01-01 12:10:00",
            ],
            "start_station_name": ["A", "B", "A"],
            "end_station_name": ["C", "D", "E"],
            "member_casual": ["member", "casual", "member"],
        }
    )

    cleaned = clean_trip_data(data)
    result = summarize_by_member_type(cleaned)

    member_row = result[result["member_casual"] == "member"].iloc[0]
    casual_row = result[result["member_casual"] == "casual"].iloc[0]

    assert member_row["total_rides"] == 2
    assert member_row["average_ride_length"] == 15
    assert casual_row["total_rides"] == 1
    assert casual_row["median_ride_length"] == 40
