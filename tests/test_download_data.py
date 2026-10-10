from pathlib import Path
from zipfile import ZipFile

import pytest

from src.download_data import (
    DivvyDataset,
    acquire_dataset,
    acquire_missing_datasets,
    compare_local_snapshot,
    extract_dataset_csv,
    get_month_from_raw_csv,
    parse_dataset_listing,
    select_latest_datasets,
    validate_downloaded_csv,
)


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


def make_zip_file(zip_path: Path, member_name: str, contents: str) -> None:
    with ZipFile(zip_path, "w") as archive:
        archive.writestr(member_name, contents)


def make_s3_listing(keys: list[str], continuation_token: str | None = None) -> str:
    contents = "\n".join(
        f"""
        <Contents>
            <Key>{key}</Key>
            <LastModified>2026-01-01T00:00:00.000Z</LastModified>
            <Size>12345</Size>
        </Contents>
        """
        for key in keys
    )
    next_token = ""
    if continuation_token:
        next_token = f"<NextContinuationToken>{continuation_token}</NextContinuationToken>"

    return f"""
    <ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
        {contents}
        {next_token}
    </ListBucketResult>
    """


def test_parse_dataset_listing_keeps_only_monthly_divvy_zip_files():
    xml_text = make_s3_listing(
        [
            "202512-divvy-tripdata.zip",
            "202601-divvy-tripdata.zip",
            "readme.txt",
            "Divvy_Trips_2019_Q1.zip",
        ]
    )

    datasets, next_token = parse_dataset_listing(xml_text)

    assert next_token is None
    assert [dataset.month for dataset in datasets] == ["2025-12", "2026-01"]
    assert datasets[0].key == "202512-divvy-tripdata.zip"
    assert datasets[0].url == "https://divvy-tripdata.s3.amazonaws.com/202512-divvy-tripdata.zip"


def test_parse_dataset_listing_returns_continuation_token_when_present():
    xml_text = make_s3_listing(["202601-divvy-tripdata.zip"], continuation_token="next-page")

    datasets, next_token = parse_dataset_listing(xml_text)

    assert len(datasets) == 1
    assert next_token == "next-page"


def test_select_latest_datasets_returns_newest_months_in_order():
    xml_text = make_s3_listing(
        [
            "202501-divvy-tripdata.zip",
            "202502-divvy-tripdata.zip",
            "202503-divvy-tripdata.zip",
            "202504-divvy-tripdata.zip",
        ]
    )
    datasets, _ = parse_dataset_listing(xml_text)

    latest_datasets = select_latest_datasets(datasets, dataset_count=3)

    assert [dataset.month for dataset in latest_datasets] == [
        "2025-02",
        "2025-03",
        "2025-04",
    ]


def test_select_latest_datasets_rejects_invalid_count():
    with pytest.raises(ValueError, match="dataset_count"):
        select_latest_datasets([], dataset_count=0)


def test_get_month_from_raw_csv_reads_official_monthly_filename(tmp_path):
    file_path = tmp_path / "202601-divvy-tripdata.csv"

    month = get_month_from_raw_csv(file_path)

    assert month == "2026-01"


def test_get_month_from_raw_csv_ignores_unrecognized_filename(tmp_path):
    file_path = tmp_path / "sample_trips.csv"

    month = get_month_from_raw_csv(file_path)

    assert month is None


def test_compare_local_snapshot_when_current(tmp_path):
    required_datasets = [
        make_dataset("2026-01"),
        make_dataset("2026-02"),
        make_dataset("2026-03"),
    ]
    for dataset in required_datasets:
        (tmp_path / dataset.key.replace(".zip", ".csv")).write_text("ride_id\n")

    comparison = compare_local_snapshot(required_datasets, tmp_path)

    assert sorted(comparison.reusable_files) == ["2026-01", "2026-02", "2026-03"]
    assert comparison.missing_datasets == []
    assert comparison.obsolete_files == []
    assert comparison.unrecognized_files == []


def test_compare_local_snapshot_identifies_missing_months(tmp_path):
    required_datasets = [
        make_dataset("2026-01"),
        make_dataset("2026-02"),
        make_dataset("2026-03"),
    ]
    (tmp_path / "202601-divvy-tripdata.csv").write_text("ride_id\n")
    (tmp_path / "202603-divvy-tripdata.csv").write_text("ride_id\n")

    comparison = compare_local_snapshot(required_datasets, tmp_path)

    assert sorted(comparison.reusable_files) == ["2026-01", "2026-03"]
    assert [dataset.month for dataset in comparison.missing_datasets] == ["2026-02"]


def test_compare_local_snapshot_identifies_obsolete_months(tmp_path):
    required_datasets = [
        make_dataset("2026-02"),
        make_dataset("2026-03"),
    ]
    obsolete_file = tmp_path / "202601-divvy-tripdata.csv"
    obsolete_file.write_text("ride_id\n")
    (tmp_path / "202602-divvy-tripdata.csv").write_text("ride_id\n")

    comparison = compare_local_snapshot(required_datasets, tmp_path)

    assert sorted(comparison.reusable_files) == ["2026-02"]
    assert comparison.obsolete_files == [obsolete_file]


def test_compare_local_snapshot_keeps_unrecognized_files_separate(tmp_path):
    required_datasets = [make_dataset("2026-01")]
    unrecognized_file = tmp_path / "notes.csv"
    unrecognized_file.write_text("not,a,monthly,file\n")

    comparison = compare_local_snapshot(required_datasets, tmp_path)

    assert comparison.reusable_files == {}
    assert [dataset.month for dataset in comparison.missing_datasets] == ["2026-01"]
    assert comparison.obsolete_files == []
    assert comparison.unrecognized_files == [unrecognized_file]


def test_extract_dataset_csv_extracts_and_renames_monthly_csv(tmp_path):
    dataset = make_dataset("2026-01")
    zip_path = tmp_path / dataset.key
    make_zip_file(
        zip_path,
        "original-name.csv",
        "ride_id,rideable_type,started_at,ended_at,member_casual\n",
    )
    staging_folder = tmp_path / "staging"

    csv_path = extract_dataset_csv(dataset, zip_path, staging_folder)

    assert csv_path.name == "202601-divvy-tripdata.csv"
    assert (
        csv_path.read_text()
        == "ride_id,rideable_type,started_at,ended_at,member_casual\n"
    )


def test_extract_dataset_csv_rejects_zip_without_csv(tmp_path):
    dataset = make_dataset("2026-01")
    zip_path = tmp_path / dataset.key
    make_zip_file(zip_path, "readme.txt", "not csv")

    with pytest.raises(ValueError, match="No CSV file"):
        extract_dataset_csv(dataset, zip_path, tmp_path)


def test_validate_downloaded_csv_accepts_required_columns(tmp_path):
    csv_path = tmp_path / "202601-divvy-tripdata.csv"
    csv_path.write_text("ride_id,rideable_type,started_at,ended_at,member_casual\n")

    validate_downloaded_csv(csv_path)


def test_validate_downloaded_csv_rejects_missing_required_columns(tmp_path):
    csv_path = tmp_path / "202601-divvy-tripdata.csv"
    csv_path.write_text("ride_id,rideable_type,started_at,member_casual\n")

    with pytest.raises(ValueError, match="ended_at"):
        validate_downloaded_csv(csv_path)


def test_acquire_dataset_downloads_extracts_validates_and_removes_zip(tmp_path):
    source_zip = tmp_path / "source.zip"
    make_zip_file(
        source_zip,
        "inside.csv",
        "ride_id,rideable_type,started_at,ended_at,member_casual\n",
    )
    dataset = make_dataset("2026-01")
    dataset = DivvyDataset(
        month=dataset.month,
        key=dataset.key,
        url=source_zip.as_uri(),
        size=source_zip.stat().st_size,
        last_modified=dataset.last_modified,
    )
    staging_folder = tmp_path / "staging"

    csv_path = acquire_dataset(dataset, staging_folder)

    assert csv_path.name == "202601-divvy-tripdata.csv"
    assert csv_path.exists()
    assert not (staging_folder / dataset.key).exists()


def test_acquire_missing_datasets_returns_all_staged_csv_files(tmp_path):
    first_zip = tmp_path / "first.zip"
    second_zip = tmp_path / "second.zip"
    csv_header = "ride_id,rideable_type,started_at,ended_at,member_casual\n"
    make_zip_file(first_zip, "first.csv", csv_header)
    make_zip_file(second_zip, "second.csv", csv_header)
    first_dataset = make_dataset("2026-01")
    second_dataset = make_dataset("2026-02")
    datasets = [
        DivvyDataset(
            month=first_dataset.month,
            key=first_dataset.key,
            url=first_zip.as_uri(),
            size=first_zip.stat().st_size,
            last_modified=first_dataset.last_modified,
        ),
        DivvyDataset(
            month=second_dataset.month,
            key=second_dataset.key,
            url=second_zip.as_uri(),
            size=second_zip.stat().st_size,
            last_modified=second_dataset.last_modified,
        ),
    ]

    acquired_files = acquire_missing_datasets(datasets, tmp_path / "staging")

    assert [file.name for file in acquired_files] == [
        "202601-divvy-tripdata.csv",
        "202602-divvy-tripdata.csv",
    ]
