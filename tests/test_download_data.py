import pytest

from src.download_data import parse_dataset_listing, select_latest_datasets


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
