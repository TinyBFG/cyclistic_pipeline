import pandas as pd

from src.clean_data import add_analysis_fields, clean_trip_data


def test_ride_length_calculation():
    data = pd.DataFrame(
        {
            "ride_id": ["ride_1"],
            "rideable_type": ["classic_bike"],
            "started_at": ["2023-01-01 10:00:00"],
            "ended_at": ["2023-01-01 10:30:00"],
            "member_casual": ["member"],
        }
    )

    result = add_analysis_fields(data)

    assert result.loc[0, "ride_length"] == 30


def test_day_of_week_creation():
    data = pd.DataFrame(
        {
            "ride_id": ["ride_1"],
            "rideable_type": ["classic_bike"],
            "started_at": ["2023-01-02 10:00:00"],
            "ended_at": ["2023-01-02 10:30:00"],
            "member_casual": ["member"],
        }
    )

    result = add_analysis_fields(data)

    assert result.loc[0, "day_of_week"] == "Monday"


def test_invalid_rides_are_removed():
    data = pd.DataFrame(
        {
            "ride_id": ["valid", "negative", "zero"],
            "rideable_type": ["classic_bike", "classic_bike", "classic_bike"],
            "started_at": [
                "2023-01-01 10:00:00",
                "2023-01-01 11:00:00",
                "2023-01-01 12:00:00",
            ],
            "ended_at": [
                "2023-01-01 10:20:00",
                "2023-01-01 10:30:00",
                "2023-01-01 12:00:00",
            ],
            "start_station_name": ["A", "B", "C"],
            "end_station_name": ["D", "E", "F"],
            "member_casual": ["member", "casual", "member"],
        }
    )

    result = clean_trip_data(data)

    assert result["ride_id"].tolist() == ["valid"]


def test_missing_required_values_are_removed():
    data = pd.DataFrame(
        {
            "ride_id": ["valid", None],
            "rideable_type": ["classic_bike", "classic_bike"],
            "started_at": ["2023-01-01 10:00:00", "2023-01-01 10:00:00"],
            "ended_at": ["2023-01-01 10:20:00", "2023-01-01 10:20:00"],
            "start_station_name": ["A", "B"],
            "end_station_name": ["C", "D"],
            "member_casual": ["member", "casual"],
        }
    )

    result = clean_trip_data(data)

    assert len(result) == 1
    assert result.loc[0, "ride_id"] == "valid"
