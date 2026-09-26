from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


COLORS = {"casual": "#2A9D8F", "member": "#264653"}


def apply_chart_style(title: str, xlabel: str, ylabel: str) -> None:
    """Apply consistent chart labels and formatting."""
    plt.title(title, fontsize=14, weight="bold")
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(axis="y", alpha=0.25)
    plt.tight_layout()


def save_current_chart(output_folder: Path, file_name: str) -> None:
    """Save the active matplotlib chart and close it."""
    output_folder.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_folder / file_name, dpi=150, bbox_inches="tight")
    plt.close()


def plot_total_rides(member_summary: pd.DataFrame, output_folder: Path) -> None:
    """Create a bar chart of total rides by rider type."""
    plt.figure(figsize=(7, 5))
    colors = [COLORS.get(rider, "#777777") for rider in member_summary["member_casual"]]
    plt.bar(member_summary["member_casual"], member_summary["total_rides"], color=colors)
    apply_chart_style("Total Rides by Rider Type", "Rider type", "Total rides")
    save_current_chart(output_folder, "total_rides_by_rider_type.png")


def plot_average_ride_length(member_summary: pd.DataFrame, output_folder: Path) -> None:
    """Create a bar chart of average ride length by rider type."""
    plt.figure(figsize=(7, 5))
    colors = [COLORS.get(rider, "#777777") for rider in member_summary["member_casual"]]
    plt.bar(member_summary["member_casual"], member_summary["average_ride_length"], color=colors)
    apply_chart_style("Average Ride Length by Rider Type", "Rider type", "Average ride length in minutes")
    save_current_chart(output_folder, "average_ride_length_by_rider_type.png")


def plot_grouped_bar(
    dataframe: pd.DataFrame,
    index_column: str,
    title: str,
    xlabel: str,
    output_folder: Path,
    file_name: str,
) -> None:
    """Create a grouped bar chart for casual and member ride counts."""
    pivot_table = dataframe.pivot(index=index_column, columns="member_casual", values="total_rides").fillna(0)

    plt.figure(figsize=(10, 5))
    pivot_table.plot(kind="bar", color=[COLORS.get(column, "#777777") for column in pivot_table.columns])
    apply_chart_style(title, xlabel, "Total rides")
    plt.legend(title="Rider type")
    save_current_chart(output_folder, file_name)


def create_all_charts(summary_tables: dict[str, pd.DataFrame], output_folder: Path) -> None:
    """Create all charts required for the case study."""
    plot_total_rides(summary_tables["member_type_summary"], output_folder)
    plot_average_ride_length(summary_tables["member_type_summary"], output_folder)
    plot_grouped_bar(
        summary_tables["rides_by_day"],
        "day_of_week",
        "Rides by Day of Week and Rider Type",
        "Day of week",
        output_folder,
        "rides_by_day_of_week.png",
    )
    plot_grouped_bar(
        summary_tables["rides_by_month"],
        "month",
        "Rides by Month and Rider Type",
        "Month",
        output_folder,
        "rides_by_month.png",
    )
    plot_grouped_bar(
        summary_tables["rides_by_hour"],
        "hour",
        "Rides by Hour of Day and Rider Type",
        "Hour of day",
        output_folder,
        "rides_by_hour.png",
    )
    plot_grouped_bar(
        summary_tables["bike_type_usage"],
        "rideable_type",
        "Bike Type Usage by Rider Type",
        "Bike type",
        output_folder,
        "bike_type_usage_by_rider_type.png",
    )
