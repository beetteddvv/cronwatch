"""Monitor wrapper that pre-filters jobs before delegating to an inner monitor."""

from __future__ import annotations

from typing import List

from cronwatch.job_filter import JobFilter, JobFilterCriteria


class FilteredMonitor:
    """Wraps any monitor and runs checks only on jobs that match filter criteria.

    The inner monitor must expose a ``check_all`` method that accepts a list of
    job configs and a ``config`` attribute whose ``jobs`` field is iterable.
    """

    def __init__(self, inner_monitor, criteria: JobFilterCriteria) -> None:
        self._inner = inner_monitor
        self._filter = JobFilter(criteria)
        self._skipped: List = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_all(self) -> None:
        """Run checks only on jobs that satisfy the filter criteria."""
        all_jobs = list(self._inner.config.jobs)
        matched = self._filter.apply(all_jobs)
        self._skipped = self._filter.excluded(all_jobs)

        # Temporarily replace the job list on the inner monitor's config so
        # existing check_all logic sees only the filtered subset.
        original_jobs = self._inner.config.jobs
        try:
            self._inner.config.jobs = matched
            self._inner.check_all()
        finally:
            self._inner.config.jobs = original_jobs

    @property
    def skipped_jobs(self) -> List:
        """Jobs excluded by the filter in the most recent check_all call."""
        return list(self._skipped)

    @property
    def skipped_count(self) -> int:
        return len(self._skipped)
