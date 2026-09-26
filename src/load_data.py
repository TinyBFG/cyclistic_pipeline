from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {
    "ride_id",
    "rideable_type",
    "started_at",
    "ended_at",
    "start_station_name",
    "end_station_name",
    "member_casual",
}


def find_csv_files(raw_data_folder: Path) -> list[Path]:
    """Return sorted CSV files from the raw data folder."""
    return sorted(raw_data_folder.glob("*.csv"))


def validate_required_columns(dataframe: pd.DataFrame, file_path: Path) -> None:
    """Raise an error if a trip file is missing required columns."""
    missing_columns = REQUIRED_COLUMNS.difference(dataframe.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"{file_path.name} is missing required columns: {missing}")


def load_trip_data(raw_data_folder: Path) -> pd.DataFrame:
    """Load and combine all monthly Cyclistic/Divvy trip CSV files."""
    csv_files = find_csv_files(raw_data_folder)
    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in {raw_data_folder}. "
            "Download 12 months of Divvy trip data and place the CSV files there."
        )

    dataframes = []
    for file_path in csv_files:
        monthly_data = pd.read_csv(file_path)
        validate_required_columns(monthly_data, file_path)
        dataframes.append(monthly_data)

    return pd.concat(dataframes, ignore_index=True)
