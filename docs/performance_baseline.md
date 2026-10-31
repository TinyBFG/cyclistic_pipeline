# Cyclistic Pipeline Performance Baseline

## Purpose

This document records the pipeline's measured performance before targeted
optimization. It provides a comparison point for future changes; it does not claim
that the current implementation is optimized.

The baseline was collected on October 30, 2026, from Git commit `a5b2d6d`.

## Benchmark Environment

- Operating system: Windows 11, build 26200
- Python: 3.14.5
- pandas: 3.0.3
- Matplotlib: 3.10.9
- psutil: 7.2.2
- Matplotlib backend: `Agg`
- Project location: a OneDrive-synchronized folder

The OneDrive location is recorded because synchronization, antivirus scanning, and
filesystem activity could affect CSV read and write times.

## Dataset

- Monthly window: October 2025 through September 2026
- Source files: 12
- Raw rows loaded: 6,171,785
- Cleaned rows retained: 6,166,404
- Rows removed by cleaning: 5,381
- Cleaned CSV size after the final run: 985,446,524 bytes

The pipeline checked the official Divvy source before every run. The local rolling
12-month snapshot was current, so no datasets were downloaded during benchmarking.

## Procedure

The benchmark used the documented PowerShell command:

```powershell
$env:MPLBACKEND = "Agg"
python main.py --measure-performance
```

One successful warm-up run was completed before three measured runs. The warm-up
finished in 122.19 seconds with sampled peak RSS of 4,177.47 MiB and was excluded
from the baseline median.

Each measured run executed the complete production workflow: source verification,
loading, cleaning, validation, cleaned CSV export, summary-table creation and
export, and chart generation.

## Measured Results

| Run | Total runtime | Sampled peak RSS |
| --- | ---: | ---: |
| 1 | 112.41 s | 4,065.60 MiB |
| 2 | 139.44 s | 4,924.32 MiB |
| 3 | 160.44 s | 4,125.76 MiB |
| **Median** | **139.44 s** | **4,125.76 MiB** |

### Stage Timings

| Stage | Run 1 | Run 2 | Run 3 | Median |
| --- | ---: | ---: | ---: | ---: |
| Prepare project folders | 0.00 s | 0.00 s | 0.00 s | 0.00 s |
| Refresh raw-data snapshot | 0.34 s | 0.30 s | 0.28 s | 0.30 s |
| Load raw trip data | 23.67 s | 27.12 s | 33.34 s | 27.12 s |
| Clean and prepare trip data | 26.05 s | 29.66 s | 36.54 s | 29.66 s |
| Validate cleaned data | 0.05 s | 0.05 s | 0.05 s | 0.05 s |
| Export cleaned data | 48.36 s | 61.76 s | 70.82 s | 61.76 s |
| Create summary tables | 8.37 s | 12.10 s | 9.67 s | 9.67 s |
| Save summary tables | 0.03 s | 0.02 s | 0.02 s | 0.02 s |
| Create charts | 2.89 s | 4.18 s | 3.23 s | 3.23 s |

## Interpretation

The cleaned CSV export is the largest measured stage at a median of 61.76 seconds,
approximately 44% of median total runtime. Cleaning has a median of 29.66 seconds
and loading has a median of 27.12 seconds. Together, loading, cleaning, and export
represent approximately 85% of median runtime when calculated from their median
stage values.

Median sampled peak RSS was 4,125.76 MiB, approximately 4.03 GiB. This is enough
memory pressure to justify investigating DataFrame allocation and lifetime before
assuming that runtime is the only optimization objective.

Total runtime ranged from 112.41 to 160.44 seconds, a difference of 48.03 seconds.
The export, cleaning, and loading stages all varied between runs. The measurements
identify areas for investigation, but they do not establish whether the variation
was caused by Python execution, storage activity, OneDrive, antivirus scanning,
memory paging, or other system workload.

## Limitations

- Three measured runs provide an initial baseline, not a comprehensive statistical
  performance study.
- Peak RSS was sampled periodically and may miss short-lived memory spikes.
- The benchmark did not collect CPU utilization, disk throughput, page faults, or
  stage-specific peak memory.
- Median stage values were calculated independently and may come from different
  runs, so they are not expected to sum exactly to median total runtime.
- The benchmark was collected from a OneDrive-synchronized project directory.

## Requirements for Future Comparisons

Future optimization results should use the same dataset window, output behavior,
Python environment, Matplotlib backend, and repeated-run procedure. Analytical
outputs must remain equivalent, and runtime or memory improvements should be large
enough to distinguish from the variability observed in this baseline.

Before selecting a targeted optimization, useful additional evidence includes
stage-level memory attribution, DataFrame memory usage by column, and CPU and disk
activity during loading, cleaning, and export.
