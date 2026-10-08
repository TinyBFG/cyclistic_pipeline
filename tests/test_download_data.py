import pytest

from src.download_data import (
    DivvyDataset,
    compare_local_snapshot,
    get_month_from_raw_csv,
    parse_dataset_listing,
    select_latest_datasets,
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
