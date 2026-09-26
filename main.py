from pathlib import Path

from src.analyze_data import create_all_summary_tables, save_summary_tables
from src.clean_data import clean_trip_data
from src.load_data import load_trip_data
from src.utils import ensure_project_folders
from src.visualize_data import create_all_charts


PROJECT_ROOT = Path(__file__).resolve().parent


def main() -> None:
    """Run the full Cyclistic case study workflow."""
    paths = ensure_project_folders(PROJECT_ROOT)

    print("Loading raw trip data...")
    raw_trips = load_trip_data(paths["raw_data"])

    print("Cleaning and preparing trip data...")
    cleaned_trips = clean_trip_data(raw_trips)
    cleaned_path = paths["processed_data"] / "cyclistic_cleaned.csv"
    cleaned_trips.to_csv(cleaned_path, index=False)

    print("Creating summary tables...")
    summary_tables = create_all_summary_tables(cleaned_trips)
    save_summary_tables(summary_tables, paths["tables"])

    print("Creating charts...")
    create_all_charts(summary_tables, paths["charts"])

    print("Analysis complete.")
    print(f"Cleaned data: {cleaned_path}")
    print(f"Tables: {paths['tables']}")
    print(f"Charts: {paths['charts']}")


if __name__ == "__main__":
    main()
