from pathlib import Path

from src.analyze_data import create_all_summary_tables, save_summary_tables
from src.clean_data import clean_trip_data
from src.load_data import find_csv_files, load_trip_data
from src.utils import ensure_project_folders


PROJECT_ROOT = Path(__file__).resolve().parent
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

        stage = "loading raw trip data"
        print("Loading raw trip data...")
        raw_trips = load_trip_data(paths["raw_data"])

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
    print(f"Source files processed: {len(find_csv_files(paths["raw_data"]))}")
    print(f"Raw rows loaded: {raw_row_count}")
    print(f"Cleaned rows retained: {cleaned_row_count}")
    print(f"Rows removed: {raw_row_count - cleaned_row_count}")
    print(f"Cleaned data: {cleaned_path}")
    print(f"Tables: {paths['tables']}")
    print(f"Charts: {paths['charts']}")


if __name__ == "__main__":
    main()
