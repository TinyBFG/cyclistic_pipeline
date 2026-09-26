from pathlib import Path


DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

MONTH_ORDER = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

RIDER_ORDER = ["casual", "member"]


def ensure_project_folders(project_root: Path) -> dict[str, Path]:
    """Create expected project folders and return their paths."""
    paths = {
        "raw_data": project_root / "data" / "raw",
        "processed_data": project_root / "data" / "processed",
        "sample_data": project_root / "data" / "sample",
        "charts": project_root / "outputs" / "charts",
        "tables": project_root / "outputs" / "tables",
        "final_report": project_root / "outputs" / "final_report",
        "docs": project_root / "docs",
    }

    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)

    return paths
