from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET
from zipfile import BadZipFile, ZipFile
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd

from src.load_data import validate_required_columns


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


def download_dataset_zip(dataset: DivvyDataset, staging_folder: Path) -> Path:
    """Download one dataset ZIP file into a staging folder."""
    staging_folder.mkdir(parents=True, exist_ok=True)
    zip_path = staging_folder / dataset.key

    try:
        with urlopen(dataset.url, timeout=120) as response:
            with zip_path.open("wb") as output_file:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    output_file.write(chunk)
    except OSError as error:
        raise RuntimeError(f"Failed to download {dataset.key}: {error}") from error

    if not zip_path.exists() or zip_path.stat().st_size == 0:
        raise ValueError(f"Downloaded file is empty: {zip_path}")

    return zip_path


def extract_dataset_csv(
    dataset: DivvyDataset, zip_path: Path, staging_folder: Path
) -> Path:
    """Extract one monthly CSV from a downloaded Divvy ZIP file."""
    staging_folder.mkdir(parents=True, exist_ok=True)
    csv_path = staging_folder / get_csv_name_for_dataset(dataset)

    try:
        with ZipFile(zip_path) as archive:
            csv_names = [
                name for name in archive.namelist() if name.lower().endswith(".csv")
            ]
            if not csv_names:
                raise ValueError(f"No CSV file found inside {zip_path.name}.")

            with archive.open(csv_names[0]) as source_file:
                with csv_path.open("wb") as output_file:
                    shutil.copyfileobj(source_file, output_file)
    except BadZipFile as error:
        raise ValueError(f"Downloaded file is not a valid ZIP archive: {zip_path}") from error

    if not csv_path.exists() or csv_path.stat().st_size == 0:
        raise ValueError(f"Extracted CSV is empty: {csv_path}")

    return csv_path


def validate_downloaded_csv(csv_path: Path) -> None:
    """Validate that a staged CSV has the required Cyclistic columns."""
    try:
        header = pd.read_csv(csv_path, nrows=0)
    except Exception as error:
        raise ValueError(f"Could not read CSV header from {csv_path.name}: {error}") from error

    validate_required_columns(header, csv_path)


def acquire_dataset(dataset: DivvyDataset, staging_folder: Path) -> Path:
    """Download, extract, and validate one dataset into the staging folder."""
    zip_path = download_dataset_zip(dataset, staging_folder)
    csv_path = extract_dataset_csv(dataset, zip_path, staging_folder)
    validate_downloaded_csv(csv_path)
    zip_path.unlink(missing_ok=True)
    return csv_path


def acquire_missing_datasets(
    missing_datasets: list[DivvyDataset], staging_folder: Path
) -> list[Path]:
    """Acquire all missing datasets into a staging folder."""
    acquired_files = []

    for dataset in missing_datasets:
        acquired_files.append(acquire_dataset(dataset, staging_folder))

    return acquired_files


def get_csv_name_for_dataset(dataset: DivvyDataset) -> str:
    """Return the expected CSV filename for a monthly Divvy dataset."""
    return dataset.key.replace(".zip", ".csv")


def build_snapshot_source_map(
    required_datasets: list[DivvyDataset],
    reusable_files: dict[str, Path],
    acquired_files: list[Path],
) -> dict[str, Path]:
    """Match each desired monthly CSV name to an existing validated source file."""
    acquired_files_by_name = {file_path.name: file_path for file_path in acquired_files}
    snapshot_sources = {}

    for dataset in required_datasets:
        csv_name = get_csv_name_for_dataset(dataset)
        source_file = reusable_files.get(dataset.month)

        if source_file is None:
            source_file = acquired_files_by_name.get(csv_name)

        if source_file is None:
            raise ValueError(
                f"Cannot refresh raw snapshot; missing validated CSV for {dataset.month}."
            )

        validate_downloaded_csv(source_file)
        snapshot_sources[csv_name] = source_file

    return snapshot_sources


def refresh_raw_data_snapshot(
    required_datasets: list[DivvyDataset],
    comparison: SnapshotComparison,
    acquired_files: list[Path],
    raw_data_folder: Path,
    staging_folder: Path,
) -> list[Path]:
    """Safely replace the active raw-data snapshot with the desired monthly files."""
    raw_data_folder.mkdir(parents=True, exist_ok=True)
    staging_folder.mkdir(parents=True, exist_ok=True)

    snapshot_sources = build_snapshot_source_map(
        required_datasets,
        comparison.reusable_files,
        acquired_files,
    )
    replacement_folder = staging_folder / "raw_snapshot_replacement"
    backup_folder = staging_folder / "raw_snapshot_backup"

    if replacement_folder.exists():
        shutil.rmtree(replacement_folder)
    if backup_folder.exists():
        shutil.rmtree(backup_folder)

    replacement_folder.mkdir(parents=True)
    backup_folder.mkdir(parents=True)

    for csv_name, source_file in snapshot_sources.items():
        destination = replacement_folder / csv_name
        shutil.copy2(source_file, destination)
        validate_downloaded_csv(destination)

    for existing_file in sorted(raw_data_folder.glob("*.csv")):
        shutil.copy2(existing_file, backup_folder / existing_file.name)

    try:
        for existing_file in sorted(raw_data_folder.glob("*.csv")):
            existing_file.unlink()

        for replacement_file in sorted(replacement_folder.glob("*.csv")):
            shutil.copy2(replacement_file, raw_data_folder / replacement_file.name)
    except OSError as error:
        for partial_file in sorted(raw_data_folder.glob("*.csv")):
            partial_file.unlink()
        for backup_file in sorted(backup_folder.glob("*.csv")):
            shutil.copy2(backup_file, raw_data_folder / backup_file.name)
        raise RuntimeError(
            "Failed to update raw-data snapshot; previous snapshot was restored."
        ) from error
    finally:
        shutil.rmtree(replacement_folder, ignore_errors=True)
        shutil.rmtree(backup_folder, ignore_errors=True)

    return sorted(raw_data_folder.glob("*.csv"))
