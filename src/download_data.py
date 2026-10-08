from dataclasses import dataclass
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from urllib.request import urlopen


DIVVY_BUCKET_URL = "https://divvy-tripdata.s3.amazonaws.com"
MONTHLY_DATASET_PATTERN = re.compile(
    r"^(?P<year>20\d{2})(?P<month>0[1-9]|1[0-2])-divvy-tripdata\.zip$"
)
LOCAL_MONTHLY_CSV_PATTERN = re.compile(
    r"^(?P<year>20\d{2})(?P<month>0[1-9]|1[0-2])-divvy-tripdata\.csv$"
)
S3_NAMESPACE = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}


@dataclass(frozen=True)
class DivvyDataset:
    """Information about one official monthly Divvy dataset."""

    month: str
    key: str
    url: str
    size: int
    last_modified: str


@dataclass(frozen=True)
class SnapshotComparison:
    """Comparison between desired official months and local raw CSV files."""

    reusable_files: dict[str, Path]
    missing_datasets: list[DivvyDataset]
    obsolete_files: list[Path]
    unrecognized_files: list[Path]


def build_bucket_listing_url(continuation_token: str | None = None) -> str:
    """Build the official S3 listing URL for the Divvy trip-data bucket."""
    query_parameters = {"list-type": "2"}
    if continuation_token:
        query_parameters["continuation-token"] = continuation_token

    return f"{DIVVY_BUCKET_URL}?{urlencode(query_parameters)}"


def fetch_bucket_listing_xml(continuation_token: str | None = None) -> str:
    """Fetch one XML page from the official Divvy S3 bucket listing."""
    listing_url = build_bucket_listing_url(continuation_token)
    with urlopen(listing_url, timeout=30) as response:
        return response.read().decode("utf-8")


def parse_dataset_listing(xml_text: str) -> tuple[list[DivvyDataset], str | None]:
    """Parse monthly Divvy datasets from one S3 bucket-listing XML page."""
    root = ET.fromstring(xml_text)
    datasets = []

    for contents in root.findall("s3:Contents", S3_NAMESPACE):
        key = contents.findtext("s3:Key", default="", namespaces=S3_NAMESPACE)
        match = MONTHLY_DATASET_PATTERN.match(key)
        if not match:
            continue

        month = f"{match.group('year')}-{match.group('month')}"
        datasets.append(
            DivvyDataset(
                month=month,
                key=key,
                url=f"{DIVVY_BUCKET_URL}/{key}",
                size=int(contents.findtext("s3:Size", default="0", namespaces=S3_NAMESPACE)),
                last_modified=contents.findtext(
                    "s3:LastModified", default="", namespaces=S3_NAMESPACE
                ),
            )
        )

    next_token = root.findtext(
        "s3:NextContinuationToken", default=None, namespaces=S3_NAMESPACE
    )
    return sorted(datasets, key=lambda dataset: dataset.month), next_token


def fetch_available_datasets() -> list[DivvyDataset]:
    """Return all official monthly Divvy datasets currently listed by the source."""
    datasets = []
    continuation_token = None

    while True:
        xml_text = fetch_bucket_listing_xml(continuation_token)
        page_datasets, continuation_token = parse_dataset_listing(xml_text)
        datasets.extend(page_datasets)

        if not continuation_token:
            break

    return sorted(datasets, key=lambda dataset: dataset.month)


def select_latest_datasets(
    available_datasets: list[DivvyDataset], dataset_count: int = 12
) -> list[DivvyDataset]:
    """Select the most recent monthly datasets from the available source list."""
    if dataset_count < 1:
        raise ValueError("dataset_count must be at least 1.")

    return sorted(available_datasets, key=lambda dataset: dataset.month)[-dataset_count:]


def get_month_from_raw_csv(file_path: Path) -> str | None:
    """Return the YYYY-MM month from a local monthly Divvy CSV filename."""
    match = LOCAL_MONTHLY_CSV_PATTERN.match(file_path.name)
    if not match:
        return None

    return f"{match.group('year')}-{match.group('month')}"


def find_local_monthly_files(raw_data_folder: Path) -> dict[str, Path]:
    """Return recognized local monthly Divvy CSV files by month."""
    local_files = {}

    for file_path in sorted(raw_data_folder.glob("*.csv")):
        month = get_month_from_raw_csv(file_path)
        if month:
            local_files[month] = file_path

    return local_files


def find_unrecognized_csv_files(raw_data_folder: Path) -> list[Path]:
    """Return local CSV files that do not match the official monthly filename pattern."""
    unrecognized_files = []

    for file_path in sorted(raw_data_folder.glob("*.csv")):
        if get_month_from_raw_csv(file_path) is None:
            unrecognized_files.append(file_path)

    return unrecognized_files


def compare_local_snapshot(
    required_datasets: list[DivvyDataset], raw_data_folder: Path
) -> SnapshotComparison:
    """Compare desired official datasets with local raw CSV files."""
    local_files = find_local_monthly_files(raw_data_folder)
    required_months = {dataset.month for dataset in required_datasets}

    reusable_files = {
        month: file_path
        for month, file_path in local_files.items()
        if month in required_months
    }
    missing_datasets = [
        dataset
        for dataset in required_datasets
        if dataset.month not in local_files
    ]
    obsolete_files = [
        file_path
        for month, file_path in local_files.items()
        if month not in required_months
    ]

    return SnapshotComparison(
        reusable_files=reusable_files,
        missing_datasets=missing_datasets,
        obsolete_files=obsolete_files,
        unrecognized_files=find_unrecognized_csv_files(raw_data_folder),
    )
