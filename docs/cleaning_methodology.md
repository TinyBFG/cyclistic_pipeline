# Cleaning Methodology

This document explains how the project cleans and prepares Cyclistic/Divvy trip data for analysis.

## 1. Combine Monthly Files

All CSV files in `data/raw/` are loaded and combined into one dataset. The files are sorted by name before loading so the process is predictable.

## 2. Validate Required Columns

Each file must include the columns needed for the case study:

- `ride_id`
- `rideable_type`
- `started_at`
- `ended_at`
- `start_station_name`
- `end_station_name`
- `member_casual`

If a file is missing one of these columns, the project stops and reports the missing column.

## 3. Remove Duplicate Rides

Duplicate rows with the same `ride_id` are removed. Each ride should appear only once in the final analysis dataset.

## 4. Convert Date and Time Fields

The `started_at` and `ended_at` columns are converted into datetime values. Rows with invalid date or time values are removed because ride duration and time-based analysis depend on these fields.

## 5. Create Analysis Fields

The project creates four fields required for analysis:

- `ride_length`: ride duration in minutes
- `day_of_week`: weekday name from the start time
- `month`: month name from the start time
- `hour`: hour of day from the start time

## 6. Remove Invalid Rides

The project removes rows when:

- required fields are missing
- `member_casual` is not `casual` or `member`
- `ride_length` is zero or negative
- `ride_length` is longer than 24 hours

These rules remove records that are incomplete, malformed, or unlikely to represent normal customer rides.

## 7. Preserve Station Fields for Station Analysis

Missing station names are not used in top station tables. This keeps the station rankings focused on known station names while still allowing valid ride records to remain available for other analyses.

## 8. Export Cleaned Data

The cleaned dataset is exported to:

`data/processed/cyclistic_cleaned.csv`
