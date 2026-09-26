import pandas as pd

# Line 59 needs to be checked


# Thought about including the station names but the
# ones without station names might still contain time
# and type information that will be useful
REQUIRED_NON_NULL_COLUMNS = [
    "ride_id",
    "rideable_type",
    "started_at",
    "ended_at",
    "member_casual",
]


def add_analysis_fields(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Add ride_length, day_of_week, month, and hour fields."""
    # Function serves two fold purposes for the started at and ended at fields
    # By formatting them you prepare them for calculation of new columns
    # and set up dropna for success with "coerce" taking non dt values and making them NaT
    trips = dataframe.copy()
    trips["started_at"] = pd.to_datetime(trips["started_at"], errors="coerce")
    trips["ended_at"] = pd.to_datetime(trips["ended_at"], errors="coerce")

    trips["ride_length"] = (
        trips["ended_at"] - trips["started_at"]
    ).dt.total_seconds() / 60
    trips["day_of_week"] = trips["started_at"].dt.day_name()
    trips["month"] = trips["started_at"].dt.month_name()
    trips["hour"] = trips["started_at"].dt.hour

    return trips


def remove_invalid_rides(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Remove rows that cannot support reliable analysis."""
    trips = dataframe.copy()

    # subset is specifically looking for null values in the required columns
    trips = trips.dropna(subset=REQUIRED_NON_NULL_COLUMNS)
    trips = trips.dropna(subset=["ride_length"])

    # Checks if each value in column is in isin() list
    # Divvy data sometimes contains test, maintenance, or malformed rides.
    trips = trips[trips["member_casual"].isin(["casual", "member"])]
    trips = trips[trips["ride_length"] > 0]
    trips = trips[trips["ride_length"] <= 24 * 60]

    trips = trips.drop_duplicates(subset=["ride_id"])
    # drop refers to the index column and unless needed extra columns unhelpful
    return trips.reset_index(drop=True)


def clean_trip_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Clean raw Cyclistic/Divvy trip data and create analysis fields."""
    trips = dataframe.copy()
    # experimenting with location trips = trips.drop_duplicates(subset=["ride_id"])
    trips = add_analysis_fields(trips)
    trips = remove_invalid_rides(trips)

    selected_columns = [
        "ride_id",
        "rideable_type",
        "started_at",
        "ended_at",
        "start_station_name",
        "end_station_name",
        "member_casual",
        "ride_length",
        "day_of_week",
        "month",
        "hour",
    ]
    available_columns = [
        column for column in selected_columns if column in trips.columns
    ]
    return trips[available_columns]
