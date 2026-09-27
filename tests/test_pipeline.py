import pandas as pd
import pytest

import main
from src.load_data import load_trip_data


def write_trip_csv(path, rows):
    pd.DataFrame(rows).to_csv(path, index=False)


def valid_trip_rows():
    return [
        {
            "ride_id": "ride_1",
            "rideable_type": "classic_bike",
            "started_at": "2023-01-01 10:00:00",
            "ended_at": "2023-01-01 10:30:00",
            "start_station_name": "Station A",
            "end_station_name": "Station B",
            "member_casual": "member",
        },
        {
            "ride_id": "ride_2",
            "rideable_type": "electric_bike",
            "started_at": "2023-01-02 11:00:00",
            "ended_at": "2023-01-02 11:45:00",
            "start_station_name": "Station C",
            "end_station_name": "Station D",
            "member_casual": "casual",
        },
    ]


def test_main_fails_clearly_when_no_raw_csv_files_exist(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "PROJECT_ROOT", tmp_path)

    with pytest.raises(FileNotFoundError, match="No CSV files found"):
        main.main()


def test_missing_required_input_columns_identifies_file_and_columns(tmp_path):
    raw_folder = tmp_path / "data" / "raw"
    raw_folder.mkdir(parents=True)
    bad_file = raw_folder / "bad_month.csv"
    write_trip_csv(
        bad_file,
        [
            {
                "ride_id": "ride_1",
                "rideable_type": "classic_bike",
                "started_at": "2023-01-01 10:00:00",
                "member_casual": "member",
            }
        ],
    )

    with pytest.raises(ValueError, match="bad_month.csv.*ended_at"):
        load_trip_data(raw_folder)


def test_main_processes_valid_raw_data_and_creates_outputs(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "PROJECT_ROOT", tmp_path)

    raw_folder = tmp_path / "data" / "raw"
    raw_folder.mkdir(parents=True)
    write_trip_csv(raw_folder / "202301-divvy-tripdata.csv", valid_trip_rows())

    main.main()

    assert (tmp_path / "data" / "processed" / "cyclistic_cleaned.csv").exists()
    assert (tmp_path / "outputs" / "tables" / "member_type_summary.csv").exists()
    assert (tmp_path / "outputs" / "charts" / "total_rides_by_rider_type.png").exists()


def test_processed_data_validation_rejects_invalid_ride_lengths():
    data = pd.DataFrame(
        {
            "ride_id": ["ride_1"],
            "rideable_type": ["classic_bike"],
            "started_at": pd.to_datetime(["2023-01-01 10:00:00"]),
            "ended_at": pd.to_datetime(["2023-01-01 09:00:00"]),
            "member_casual": ["member"],
            "ride_length": [-60],
            "day_of_week": ["Sunday"],
            "month": ["January"],
            "hour": [10],
        }
    )

    with pytest.raises(ValueError, match="invalid ride durations"):
        main.validate_processed_data(data)
