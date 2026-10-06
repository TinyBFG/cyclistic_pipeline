from dataclasses import dataclass
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from urllib.request import urlopen


DIVVY_BUCKET_URL = "https://divvy-tripdata.s3.amazonaws.com"
MONTHLY_DATASET_PATTERN = re.compile(
    r"^(?P<year>20\d{2})(?P<month>0[1-9]|1[0-2])-divvy-tripdata\.zip$"
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
