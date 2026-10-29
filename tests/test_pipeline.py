import pandas as pd
import pytest

import main
from src.download_data import DivvyDataset
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


def make_dataset(month: str) -> DivvyDataset:
    key_month = month.replace("-", "")
    key = f"{key_month}-divvy-tripdata.zip"
    return DivvyDataset(
        month=month,
        key=key,
        url=f"https://divvy-tripdata.s3.amazonaws.com/{key}",
        size=12345,
        last_modified="2026-01-01T00:00:00.000Z",
    )


def mock_current_raw_snapshot(monkeypatch, months: list[str]) -> None:
    datasets = [make_dataset(month) for month in months]

    monkeypatch.setattr(main, "RAW_DATASET_COUNT", len(datasets))
    monkeypatch.setattr(main, "fetch_available_datasets", lambda: datasets)


def test_main_fails_clearly_when_no_official_datasets_exist(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(main, "fetch_available_datasets", lambda: [])

    with pytest.raises(ValueError, match="No monthly Divvy datasets"):
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
    mock_current_raw_snapshot(monkeypatch, ["2023-01"])

    raw_folder = tmp_path / "data" / "raw"
    raw_folder.mkdir(parents=True)
    write_trip_csv(raw_folder / "202301-divvy-tripdata.csv", valid_trip_rows())

    metrics = main.main(measure_performance=True)

    assert (tmp_path / "data" / "processed" / "cyclistic_cleaned.csv").exists()
    assert (tmp_path / "outputs" / "tables" / "member_type_summary.csv").exists()
    assert (tmp_path / "outputs" / "charts" / "total_rides_by_rider_type.png").exists()
    assert set(metrics.stage_timings) == {
        "preparing project folders",
        "refreshing raw data snapshot",
        "loading raw trip data",
        "cleaning and preparing trip data",
        "validating cleaned data",
        "exporting cleaned data",
        "creating summary tables",
        "saving summary tables",
        "creating charts",
    }
    assert all(duration >= 0 for duration in metrics.stage_timings.values())
    assert metrics.total_runtime_seconds is not None
    assert metrics.total_runtime_seconds >= sum(metrics.stage_timings.values())
    assert metrics.sampled_peak_rss_bytes is not None
    assert metrics.sampled_peak_rss_bytes > 0


def test_main_downloads_missing_data_before_loading(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "PROJECT_ROOT", tmp_path)
    mock_current_raw_snapshot(monkeypatch, ["2023-01"])
    csv_header = (
        "ride_id,rideable_type,started_at,ended_at,"
        "start_station_name,end_station_name,member_casual\n"
    )
    csv_row = (
        "ride_1,classic_bike,2023-01-01 10:00:00,2023-01-01 10:30:00,"
        "Station A,Station B,member\n"
    )

    def fake_acquire_missing_datasets(missing_datasets, staging_folder):
        staging_folder.mkdir(parents=True, exist_ok=True)
        acquired_files = []
        for dataset in missing_datasets:
            csv_path = staging_folder / dataset.key.replace(".zip", ".csv")
            csv_path.write_text(csv_header + csv_row)
            acquired_files.append(csv_path)
        return acquired_files

    monkeypatch.setattr(
        main,
        "acquire_missing_datasets",
        fake_acquire_missing_datasets,
    )

    metrics = main.main()

    assert (tmp_path / "data" / "raw" / "202301-divvy-tripdata.csv").exists()
    assert (tmp_path / "data" / "processed" / "cyclistic_cleaned.csv").exists()
    assert metrics.stage_timings == {}
    assert metrics.total_runtime_seconds is None
    assert metrics.sampled_peak_rss_bytes is None


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
