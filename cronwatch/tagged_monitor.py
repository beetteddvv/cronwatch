"""Monitor variant that respects tag-based job filtering."""

from typing import List, Optional

from cronwatch.monitor import Monitor
from cronwatch.tag_filter import TagFilter, TagFilterManager


class TaggedMonitor:
    """Wraps Monitor and only checks jobs that match the given TagFilter."""

    def __init__(
        self,
        monitor: Monitor,
        tag_filter: Optional[TagFilter] = None,
    ) -> None:
        self._monitor = monitor
        self._mgr = TagFilterManager(tag_filter)
        self._skipped: List[str] = []

    def check_all(self) -> None:
        """Run checks only for jobs that pass the tag filter."""
        self._skipped = []
        all_jobs = self._monitor.config.jobs
        matched = self._mgr.filter_jobs(all_jobs)
        skipped_names = {
            j.name for j in all_jobs
        } - {j.name for j in matched}
        self._skipped = list(skipped_names)

        # Temporarily swap the job list so Monitor.check_all sees only matched
        original_jobs = self._monitor.config.jobs
        self._monitor.config.jobs = matched
        try:
            self._monitor.check_all()
        finally:
            self._monitor.config.jobs = original_jobs

    @property
    def skipped_jobs(self) -> List[str]:
        """Names of jobs skipped due to tag filtering in the last check_all."""
        return list(self._skipped)

    @property
    def skipped_count(self) -> int:
        return len(self._skipped)
