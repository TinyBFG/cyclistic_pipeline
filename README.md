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
│   ├── raw/          # Place the 12 monthly trip CSV files here
│   ├── processed/    # Cleaned combined dataset is exported here
│   └── sample/       # Small sample data for tests and examples
├── docs/
│   ├── cleaning_methodology.md
│   └── final_case_study.md
├── outputs/
│   ├── charts/       # Exported PNG visualizations
│   ├── tables/       # Exported CSV summary tables
│   └── final_report/ # Optional location for final report exports
├── src/
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

Download 12 months of Divvy trip data from:

https://divvy-tripdata.s3.amazonaws.com/index.html

Place the monthly `.csv` files in `data/raw/`. Do not unzip nested folders into `data/raw/`; the CSV files should be directly inside that folder.

## How to Run the Project

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Add 12 monthly Divvy trip CSV files to `data/raw/`.

3. Run the full analysis:

```bash
python main.py
```

The script creates:

- `data/processed/cyclistic_cleaned.csv`
- summary tables in `outputs/tables/`
- chart images in `outputs/charts/`

## How to Run Tests

```bash
pytest
```

The tests use small sample data and do not require the full Divvy dataset.

## Expected Outputs

The project produces:

- a clear business task statement
- a data source description
- documented cleaning and manipulation steps
- summary tables comparing casual riders and members
- polished charts for key usage patterns
- a concise final case study document
- top three recommendations

## Notes

This version focuses only on the Cyclistic case study deliverables. It does not build a dashboard or automated monthly pipeline.
