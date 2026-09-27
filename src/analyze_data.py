from pathlib import Path

import pandas as pd

from src.utils import DAY_ORDER, MONTH_ORDER


def summarize_by_member_type(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Calculate ride totals and ride length statistics by rider type."""
    summary = (
        dataframe.groupby("member_casual")
        .agg(
            total_rides=("ride_id", "count"),
            average_ride_length=("ride_length", "mean"),
            median_ride_length=("ride_length", "median"),
        )
        .reset_index()
    )
    summary["average_ride_length"] = summary["average_ride_length"].round(2)
    summary["median_ride_length"] = summary["median_ride_length"].round(2)
    return summary


def rides_by_day(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Count rides by day of week and rider type."""
    summary = (
        dataframe.groupby(["day_of_week", "member_casual"])
        .size()
        .reset_index(name="total_rides")
    )
    summary["day_of_week"] = pd.Categorical(
        summary["day_of_week"], categories=DAY_ORDER, ordered=True
    )
    return summary.sort_values(["day_of_week", "member_casual"]).reset_index(drop=True)


def rides_by_month(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Count rides by month and rider type."""
    summary = (
        dataframe.groupby(["month", "member_casual"])
        .size()
        .reset_index(name="total_rides")
    )
    summary["month"] = pd.Categorical(
        summary["month"], categories=MONTH_ORDER, ordered=True
    )
    return summary.sort_values(["month", "member_casual"]).reset_index(drop=True)


def rides_by_hour(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Count rides by hour of day and rider type."""
    return (
        dataframe.groupby(["hour", "member_casual"])
        .size()
        .reset_index(name="total_rides")
        .sort_values(["hour", "member_casual"])
        .reset_index(drop=True)
    )


def bike_type_usage(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Count bike type usage by rider type."""
    return (
        dataframe.groupby(["rideable_type", "member_casual"])
        .size()
        .reset_index(name="total_rides")
        .sort_values(["rideable_type", "member_casual"])
        .reset_index(drop=True)
    )


def top_start_stations(
    dataframe: pd.DataFrame, rider_type: str, limit: int = 10
) -> pd.DataFrame:
    """Return the most common start stations for one rider type."""
    if "start_station_name" not in dataframe.columns:
        return pd.DataFrame(columns=["start_station_name", "total_rides"])

    station_data = dataframe[
        (dataframe["member_casual"] == rider_type)
        & dataframe["start_station_name"].notna()
    ]
    return (
        station_data.groupby("start_station_name")
        .size()
        .reset_index(name="total_rides")
        .sort_values("total_rides", ascending=False)
        .head(limit)
        .reset_index(drop=True)
    )


def create_all_summary_tables(dataframe: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Create all summary tables required for the case study."""
    return {
        "member_type_summary": summarize_by_member_type(dataframe),
        "rides_by_day": rides_by_day(dataframe),
        "rides_by_month": rides_by_month(dataframe),
        "rides_by_hour": rides_by_hour(dataframe),
        "bike_type_usage": bike_type_usage(dataframe),
        "top_start_stations_casual": top_start_stations(dataframe, "casual"),
        "top_start_stations_member": top_start_stations(dataframe, "member"),
    }


def save_summary_tables(
    summary_tables: dict[str, pd.DataFrame], output_folder: Path
) -> None:
    """Export summary tables as CSV files."""
    output_folder.mkdir(parents=True, exist_ok=True)
    for table_name, table in summary_tables.items():
        table.to_csv(output_folder / f"{table_name}.csv", index=False)
