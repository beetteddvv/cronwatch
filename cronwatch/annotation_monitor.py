"""Monitor that only checks jobs matching a given annotation filter."""
from __future__ import annotations

from typing import List, Optional

from cronwatch.job_annotations import AnnotationFilter
from cronwatch.monitor import Monitor


class AnnotationMonitor:
    """Wraps an inner Monitor and skips jobs that don't match annotation criteria."""

    def __init__(self, inner: Monitor, annotation_filter: AnnotationFilter) -> None:
        self._inner = inner
        self._filter = annotation_filter
        self._skipped: List[str] = []

    @property
    def skipped_jobs(self) -> List[str]:
        return list(self._skipped)

    @property
    def skipped_count(self) -> int:
        return len(self._skipped)

    def check_all(self) -> None:
        self._skipped = []
        config = self._inner._config  # type: ignore[attr-defined]
        all_names = [job.name for job in config.jobs]
        allowed = set(self._filter.apply(all_names))

        original_jobs = config.jobs
        try:
            config.jobs = [j for j in original_jobs if j.name in allowed]
            self._skipped = [j.name for j in original_jobs if j.name not in allowed]
            self._inner.check_all()
        finally:
            config.jobs = original_jobs
