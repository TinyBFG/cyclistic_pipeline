# Cyclistic Bike-Share Case Study

This project completes the Google Data Analytics Cyclistic case study using Python.

## Business Question

How do annual members and casual riders use Cyclistic bikes differently?

## Project Purpose

The goal is to analyze 12 months of Cyclistic/Divvy trip data, compare usage patterns between annual members and casual riders, and produce clear findings and recommendations for converting casual riders into annual members.

## Folder Structure

```text
cyclistic_case_study/
├── data/
│   ├── raw/          # Active rolling 12-month raw Divvy snapshot
│   ├── processed/    # Cleaned combined dataset is exported here
│   ├── sample/       # Small sample data for tests and examples
│   └── staging/      # Temporary download/extraction workspace
├── docs/
│   ├── cleaning_methodology.md
│   └── final_case_study.md
├── outputs/
│   ├── charts/       # Exported PNG visualizations
│   ├── tables/       # Exported CSV summary tables
│   └── final_report/ # Optional location for final report exports
├── src/
│   ├── download_data.py
│   ├── load_data.py
│   ├── clean_data.py
│   ├── analyze_data.py
│   ├── visualize_data.py
│   └── utils.py
├── tests/
│   ├── test_analyze_data.py
│   └── test_clean_data.py
├── main.py
└── requirements.txt
```

## Data Source

The project uses the official Divvy trip-data source:

https://divvy-tripdata.s3.amazonaws.com/index.html

When `python main.py` runs, the pipeline checks the official source, identifies the most recent 12 published monthly datasets, and compares those months against the local files in `data/raw/`.

If the local raw-data snapshot is already current, no files are downloaded. If one or more months are missing, the pipeline downloads only the missing ZIP files, extracts the CSVs, validates the required columns, and safely refreshes `data/raw/`.

The `data/raw/` folder is treated as the active rolling 12-month snapshot used for the current analysis. It should not grow into a permanent archive of every historical month.

## How to Run the Project

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the full analysis:

```bash
python main.py
```

The script automatically prepares the latest raw Divvy data before loading, cleaning, analyzing, and visualizing the trips.

The script creates:

- the active raw snapshot in `data/raw/`
- `data/processed/cyclistic_cleaned.csv`
- summary tables in `outputs/tables/`
- chart images in `outputs/charts/`

## Performance Benchmarking

Performance measurement is optional. In PowerShell, run the full pipeline with
measurement enabled using:

```powershell
$env:MPLBACKEND = "Agg"
python main.py --measure-performance
```

`MPLBACKEND=Agg` uses Matplotlib's non-interactive chart renderer, allowing chart
generation without requiring a desktop GUI while still producing the normal PNG
chart files. The pipeline prints a concise report containing:

- elapsed time for each pipeline stage
- total pipeline runtime
- sampled peak process memory in MiB

Performance measurement does not replace or change the cleaned dataset, summary
tables, or charts.

For a comparable before-and-after benchmark:

1. Use the same computer and Python environment.
2. Confirm both runs use the same rolling 12-month window shown in the pipeline
   output.
3. Record the Git commit being measured with `git rev-parse --short HEAD`.
4. Close resource-heavy applications and keep the computer on the same power
   setting.
5. Run the command once as a warm-up, then collect at least three measured runs.
6. Compare the median total runtime and review stage timings and sampled peak
   memory for meaningful tradeoffs.

Peak memory is sampled periodically, so it is an estimate rather than a guaranteed
observation of every short-lived memory spike. Benchmark results should remain
local unless deliberately selected as a documentation artifact.

## How to Run Tests

```bash
pytest
```

The tests use small sample data and do not require the full Divvy dataset.

## Expected Outputs

The project produces:

- a clear business task statement
- a data source description
- an automated rolling 12-month raw-data snapshot
- documented cleaning and manipulation steps
- summary tables comparing casual riders and members
- polished charts for key usage patterns
- a concise final case study document
- top three recommendations

## Notes

This version focuses on a local, single-command Cyclistic pipeline. It automatically maintains the latest 12 months of official Divvy data, but it does not include scheduling, cloud deployment, or Tableau/Power BI dashboard integration yet.
