from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from threading import Event, Thread
from time import perf_counter
from types import TracebackType

import psutil


Clock = Callable[[], float]
MemoryReader = Callable[[], int]


@dataclass(frozen=True)
class PerformanceMetrics:
    """Performance measurements collected during one pipeline run."""

    stage_timings: dict[str, float]
    total_runtime_seconds: float | None
    sampled_peak_rss_bytes: int | None


def format_performance_report(metrics: PerformanceMetrics) -> str:
    """Return a concise, human-readable summary of pipeline performance."""
    total_runtime = (
        f"{metrics.total_runtime_seconds:.2f} s"
        if metrics.total_runtime_seconds is not None
        else "not measured"
    )
    peak_memory = (
        f"{metrics.sampled_peak_rss_bytes / (1024**2):.2f} MiB"
        if metrics.sampled_peak_rss_bytes is not None
        else "not measured"
    )
    lines = [
        "Performance report",
        f"Total runtime: {total_runtime}",
        f"Sampled peak memory (RSS): {peak_memory}",
    ]

    if metrics.stage_timings:
        lines.append("Stage timings:")
        lines.extend(
            f"  - {stage_name}: {duration:.2f} s"
            for stage_name, duration in metrics.stage_timings.items()
        )
    else:
        lines.append("Stage timings: not measured")

    return "\n".join(lines)


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


class PeakMemoryMonitor:
    """Sample this process's resident memory and retain the largest reading."""

    def __init__(
        self,
        enabled: bool = True,
        sample_interval_seconds: float = 0.1,
        memory_reader: MemoryReader | None = None,
    ) -> None:
        if sample_interval_seconds <= 0:
            raise ValueError("sample_interval_seconds must be greater than zero.")

        self.enabled = enabled
        self.sample_interval_seconds = sample_interval_seconds
        self.peak_rss_bytes = 0
        self._memory_reader = memory_reader
        self._process = psutil.Process() if enabled and memory_reader is None else None
        self._stop_event = Event()
        self._thread: Thread | None = None
        self._sampling_error: Exception | None = None

    @property
    def is_running(self) -> bool:
        """Return whether the sampling thread is currently active."""
        return self._thread is not None and self._thread.is_alive()

    def _read_rss_bytes(self) -> int:
        if self._memory_reader is not None:
            return self._memory_reader()

        if self._process is None:
            raise RuntimeError("Process memory reader was not initialized.")

        return self._process.memory_info().rss

    def _record_sample(self) -> None:
        current_rss_bytes = self._read_rss_bytes()
        self.peak_rss_bytes = max(self.peak_rss_bytes, current_rss_bytes)

    def _sample_until_stopped(self) -> None:
        try:
            while not self._stop_event.wait(self.sample_interval_seconds):
                self._record_sample()
        except Exception as error:
            self._sampling_error = error
            self._stop_event.set()

    def start(self) -> None:
        """Take an initial sample and start background memory sampling."""
        if not self.enabled:
            return
        if self._thread is not None:
            raise RuntimeError("Peak memory monitor has already been started.")

        self._record_sample()
        self._thread = Thread(
            target=self._sample_until_stopped,
            name="peak-memory-monitor",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop sampling, take a final sample, and surface sampling errors."""
        if not self.enabled or self._thread is None:
            return

        self._stop_event.set()
        self._thread.join()

        if self._sampling_error is not None:
            raise RuntimeError("Peak memory sampling failed.") from self._sampling_error

        self._record_sample()

    def __enter__(self) -> "PeakMemoryMonitor":
        self.start()
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            self.stop()
        except Exception:
            if exception_type is None:
                raise
