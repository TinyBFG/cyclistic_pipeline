from collections.abc import Callable

import pytest

from src.performance import measure_stage


def make_clock(readings: list[float]) -> Callable[[], float]:
    reading_iterator = iter(readings)
    return lambda: next(reading_iterator)


def test_measure_stage_records_elapsed_seconds():
    timings = {}
    clock = make_clock([10.0, 12.75])

    with measure_stage("loading raw data", timings, clock=clock):
        pass

    assert timings == {"loading raw data": 2.75}


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
