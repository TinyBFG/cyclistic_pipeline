# Cyclistic Bike-Share Case Study

## 1. Business Task

The business task is to determine how annual members and casual riders use Cyclistic bikes differently. The goal is to identify behavior patterns that can support marketing recommendations for converting casual riders into annual members.

## 2. Data Sources

The analysis uses public Cyclistic/Divvy trip data from the Divvy trip data archive:

https://divvy-tripdata.s3.amazonaws.com/index.html

The project is designed to use 12 monthly CSV files. Each file contains individual ride records, including ride ID, bike type, start time, end time, station information, and rider type.

## 3. Data Cleaning and Preparation

The data cleaning process combines the 12 monthly CSV files into one dataset, validates required columns, removes duplicate rides, converts date and time fields, and creates the fields needed for analysis.

The created analysis fields are:

- `ride_length`
- `day_of_week`
- `month`
- `hour`

Rows are removed if they are missing required values, contain invalid rider types, have invalid timestamps, have zero or negative ride lengths, or have ride lengths longer than 24 hours.

More detail is available in `docs/cleaning_methodology.md`.

## 4. Analysis Summary

The analysis compares casual riders and annual members across:

- total rides
- average ride length
- median ride length
- rides by day of week
- rides by month
- rides by hour of day
- bike type usage
- top start stations for casual riders
- top start stations for annual members

The Python workflow exports summary tables to `outputs/tables/` and charts to `outputs/charts/`.

## 5. Key Findings

After running the project with 12 months of trip data, update this section using the exported tables and charts.

Expected interpretation areas include:

- whether casual riders take longer rides than members
- whether members ride more during weekday commute hours
- whether casual riders ride more on weekends or warmer months
- whether bike type preferences differ by rider type
- which stations are most important for each group

## 6. Visualizations

The project creates the following visualizations:

- `total_rides_by_rider_type.png`
- `average_ride_length_by_rider_type.png`
- `rides_by_day_of_week.png`
- `rides_by_month.png`
- `rides_by_hour.png`
- `bike_type_usage_by_rider_type.png`

These charts are saved in `outputs/charts/`.

## 7. Top Three Recommendations

1. Promote annual memberships to casual riders who ride repeatedly on weekends or during high-demand leisure months.
2. Create campaign messaging that compares the cost of frequent casual rides with the value of an annual membership.
3. Target marketing near top casual rider start stations, especially stations with strong recreational or tourist activity.

## 8. Limitations

The public trip data does not include personally identifiable rider information, payment details, marketing exposure, or reasons for each trip. Because of this, the analysis can describe behavior patterns but cannot prove why riders choose casual passes or annual memberships.

Weather, events, tourism patterns, and service availability may also affect ridership but are not included in the base trip files.

## 9. Next Steps

Recommended next steps are to run the workflow with the selected 12 months of data, update the Key Findings section with exact results, and use the exported charts in the final portfolio submission.

Future work could include dashboard development or an automated monthly pipeline, but those are intentionally outside the scope of this case study project.
