from collections.abc import Callable
from threading import Event

import pytest

from src.performance import (
    PeakMemoryMonitor,
    PerformanceMetrics,
    format_performance_report,
    measure_stage,
)


def make_clock(readings: list[float]) -> Callable[[], float]:
    reading_iterator = iter(readings)
    return lambda: next(reading_iterator)


def test_measure_stage_records_elapsed_seconds():
    timings = {}
    clock = make_clock([10.0, 12.75])

    with measure_stage("loading raw data", timings, clock=clock):
        pass

    assert timings == {"loading raw data": 2.75}


def test_format_performance_report_uses_readable_units_and_stage_order():
    metrics = PerformanceMetrics(
        stage_timings={
            "loading raw trip data": 4.25,
            "cleaning trip data": 2.5,
        },
        total_runtime_seconds=12.345,
        sampled_peak_rss_bytes=512 * 1024**2,
    )

    report = format_performance_report(metrics)

    assert report == (
        "Performance report\n"
        "Total runtime: 12.35 s\n"
        "Sampled peak memory (RSS): 512.00 MiB\n"
        "Stage timings:\n"
        "  - loading raw trip data: 4.25 s\n"
        "  - cleaning trip data: 2.50 s"
    )


def test_measure_stage_does_nothing_when_disabled():
    timings = {}

    def unexpected_clock_call() -> float:
        raise AssertionError("The clock should not run when measurement is disabled.")

    with measure_stage(
        "loading raw data",
        timings,
        enabled=False,
        clock=unexpected_clock_call,
    ):
        pass

    assert timings == {}


def test_measure_stage_records_time_when_stage_fails():
    timings = {}
    clock = make_clock([5.0, 6.5])

    with pytest.raises(ValueError, match="example failure"):
        with measure_stage("cleaning data", timings, clock=clock):
            raise ValueError("example failure")

    assert timings == {"cleaning data": 1.5}


def test_peak_memory_monitor_records_largest_sample():
    readings = [100, 300, 200]
    reading_index = 0
    three_samples_recorded = Event()

    def read_memory() -> int:
        nonlocal reading_index
        value = readings[min(reading_index, len(readings) - 1)]
        reading_index += 1
        if reading_index >= 3:
            three_samples_recorded.set()
        return value

    monitor = PeakMemoryMonitor(
        sample_interval_seconds=0.001,
        memory_reader=read_memory,
    )

    with monitor:
        assert three_samples_recorded.wait(timeout=1)

    assert monitor.peak_rss_bytes == 300
    assert not monitor.is_running


def test_peak_memory_monitor_does_nothing_when_disabled():
    def unexpected_memory_read() -> int:
        raise AssertionError("Memory should not be read when monitoring is disabled.")

    monitor = PeakMemoryMonitor(
        enabled=False,
        memory_reader=unexpected_memory_read,
    )

    with monitor:
        pass

    assert monitor.peak_rss_bytes == 0
    assert not monitor.is_running


def test_peak_memory_monitor_rejects_invalid_interval():
    with pytest.raises(ValueError, match="greater than zero"):
        PeakMemoryMonitor(sample_interval_seconds=0)


def test_peak_memory_monitor_stops_when_measured_code_fails():
    monitor = PeakMemoryMonitor(
        sample_interval_seconds=0.001,
        memory_reader=lambda: 100,
    )

    with pytest.raises(ValueError, match="example failure"):
        with monitor:
            raise ValueError("example failure")

    assert monitor.peak_rss_bytes == 100
    assert not monitor.is_running
