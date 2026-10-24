from collections.abc import Callable, Iterator
from contextlib import contextmanager
from time import perf_counter


Clock = Callable[[], float]


@contextmanager
def measure_stage(
    stage_name: str,
    timings: dict[str, float],
    enabled: bool = True,
    clock: Clock = perf_counter,
) -> Iterator[None]:
    """Record one stage's elapsed time when performance measurement is enabled."""
    if not enabled:
        yield
        return

    start_time = clock()
    try:
        yield
    finally:
        timings[stage_name] = clock() - start_time
