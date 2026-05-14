"""Monitor wrapper that skips jobs with unmet dependencies."""

from __future__ import annotations

from typing import List, Set

from cronwatch.dependency import DependencyChecker, DependencyViolation
from cronwatch.monitor import Monitor


class DependencyAwareMonitor:
    """Wraps a Monitor and skips jobs whose dependencies haven't completed."""

    def __init__(
        self,
        monitor: Monitor,
        checker: DependencyChecker,
        completed: Set[str] | None = None,
    ) -> None:
        self._monitor = monitor
        self._checker = checker
        self._completed: Set[str] = completed if completed is not None else set()
        self._violations: List[DependencyViolation] = []

    def mark_completed(self, job_name: str) -> None:
        self._completed.add(job_name)

    def check_all(self) -> None:
        """Run check_all on the inner monitor, skipping jobs with unmet deps."""
        self._violations = []
        config = self._monitor.config

        for job in config.jobs:
            violation = self._checker.check(job.name, self._completed)
            if violation is not None:
                self._violations.append(violation)
                continue
            self._monitor._check_job(job)

    @property
    def violations(self) -> List[DependencyViolation]:
        return list(self._violations)

    @property
    def violation_count(self) -> int:
        return len(self._violations)
