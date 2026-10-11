from pathlib import Path

from src.analyze_data import create_all_summary_tables, save_summary_tables
from src.clean_data import clean_trip_data
from src.download_data import (
    DivvyDataset,
    acquire_missing_datasets,
    compare_local_snapshot,
    fetch_available_datasets,
    refresh_raw_data_snapshot,
    select_latest_datasets,
)
from src.load_data import find_csv_files, load_trip_files
from src.utils import ensure_project_folders


PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DATASET_COUNT = 12
ANALYTICAL_COLUMNS = {
    "ride_id",
    "rideable_type",
    "started_at",
    "ended_at",
    "member_casual",
    "ride_length",
    "day_of_week",
    "month",
    "hour",
}


def format_month_window(required_datasets: list[DivvyDataset]) -> str:
    """Return a readable first-month to last-month range for status output."""
    if not required_datasets:
        return "no monthly datasets found"

    return f"{required_datasets[0].month} to {required_datasets[-1].month}"


def ensure_latest_raw_snapshot(paths: dict[str, Path]) -> list[Path]:
    """Ensure data/raw contains the latest rolling Divvy raw-data snapshot."""
    print("Checking Divvy data source...")
    available_datasets = fetch_available_datasets()
    required_datasets = select_latest_datasets(
        available_datasets,
        dataset_count=RAW_DATASET_COUNT,
    )

    if not required_datasets:
        raise ValueError("No monthly Divvy datasets were found at the official source.")

    print(f"Latest available month: {required_datasets[-1].month}")
    print(f"Required window: {format_month_window(required_datasets)}")

    comparison = compare_local_snapshot(required_datasets, paths["raw_data"])
    snapshot_is_current = (
        not comparison.missing_datasets
        and not comparison.obsolete_files
        and not comparison.unrecognized_files
    )

    if snapshot_is_current:
        print("Local raw-data snapshot is current. No downloads required.")
        return find_csv_files(paths["raw_data"])

    if comparison.reusable_files:
        print(f"Reusing {len(comparison.reusable_files)} existing monthly files.")
    if comparison.missing_datasets:
        print(f"Downloading {len(comparison.missing_datasets)} missing monthly files...")
    if comparison.obsolete_files:
        print(
            f"Removing {len(comparison.obsolete_files)} obsolete monthly files "
            "after validation."
        )
    if comparison.unrecognized_files:
        print(
            f"Removing {len(comparison.unrecognized_files)} unrecognized CSV files "
            "after validation."
        )

    acquired_files = acquire_missing_datasets(
        comparison.missing_datasets,
        paths["staging_data"],
    )
    refreshed_files = refresh_raw_data_snapshot(
        required_datasets,
        comparison,
        acquired_files,
        paths["raw_data"],
        paths["staging_data"],
    )
    print("Raw-data snapshot updated successfully.")
    return refreshed_files


def validate_processed_data(dataframe) -> None:
    """Check that cleaned data is ready for analysis and export."""
    if dataframe.empty:
        raise ValueError("Cleaned dataset is empty after cleaning.")

    missing_columns = ANALYTICAL_COLUMNS.difference(dataframe.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Cleaned dataset is missing analytical columns: {missing}")

    if dataframe["started_at"].isna().any() or dataframe["ended_at"].isna().any():
        raise ValueError("Cleaned dataset still contains invalid start or end times.")

    invalid_duration_rows = dataframe[
        (dataframe["ride_length"] <= 0) | (dataframe["ride_length"] > 24 * 60)
    ]
    if not invalid_duration_rows.empty:
        raise ValueError("Cleaned dataset still contains invalid ride durations.")


def main() -> None:
    """Run the full Cyclistic case study workflow."""
    stage = "starting"
    print("Starting Cyclistic pipeline...")

    try:
        stage = "preparing project folders"
        paths = ensure_project_folders(PROJECT_ROOT)

        stage = "refreshing raw data snapshot"
        csv_files = ensure_latest_raw_snapshot(paths)
        if not csv_files:
            raise FileNotFoundError(
                f"No CSV files found in {paths['raw_data']}. "
                "The raw-data snapshot refresh did not produce input files."
            )

        stage = "loading raw trip data"
        print("Loading raw trip data...")
        raw_trips = load_trip_files(csv_files)

        stage = "cleaning and preparing trip data"
        print("Cleaning and preparing trip data...")
        cleaned_trips = clean_trip_data(raw_trips)

        stage = "validating cleaned data"
        print("Validating cleaned data...")
        validate_processed_data(cleaned_trips)

        stage = "exporting cleaned data"
        print("Exporting cleaned data...")
        cleaned_path = paths["processed_data"] / "cyclistic_cleaned.csv"
        cleaned_trips.to_csv(cleaned_path, index=False)

        stage = "creating summary tables"
        print("Creating summary tables...")
        summary_tables = create_all_summary_tables(cleaned_trips)
        save_summary_tables(summary_tables, paths["tables"])

        stage = "creating charts"
        print("Creating charts...")
        from src.visualize_data import create_all_charts

        create_all_charts(summary_tables, paths["charts"])

    except Exception as error:
        print(f"Pipeline failed while {stage}: {error}")
        raise

    raw_row_count = len(raw_trips)
    cleaned_row_count = len(cleaned_trips)

    print("Pipeline completed successfully.")
    print(f"Source files processed: {len(csv_files)}")
    print(f"Raw rows loaded: {raw_row_count}")
    print(f"Cleaned rows retained: {cleaned_row_count}")
    print(f"Rows removed: {raw_row_count - cleaned_row_count}")
    print(f"Cleaned data: {cleaned_path}")
    print(f"Tables: {paths['tables']}")
    print(f"Charts: {paths['charts']}")


if __name__ == "__main__":
    main()
