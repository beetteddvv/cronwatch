"""Job timeout tracking — flags jobs that exceeded their expected max duration."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from cronwatch.history import HistoryStore


@dataclass
class TimeoutViolation:
    job_name: str
    started_at: datetime
    duration_seconds: float
    max_duration_seconds: float

    def __str__(self) -> str:
        return (
            f"{self.job_name} ran for {self.duration_seconds:.1f}s, "
            f"exceeded limit of {self.max_duration_seconds}s"
        )


@dataclass
class TimeoutPolicy:
    max_duration_seconds: float
    job_name: Optional[str] = None  # None means applies to all jobs


class JobTimeoutChecker:
    """Checks recent job runs against configured timeout policies."""

    def __init__(self, history: HistoryStore, policies: List[TimeoutPolicy]) -> None:
        self._history = history
        self._policies: Dict[Optional[str], TimeoutPolicy] = {}
        for p in policies:
            self._policies[p.job_name] = p

    def _policy_for(self, job_name: str) -> Optional[TimeoutPolicy]:
        if job_name in self._policies:
            return self._policies[job_name]
        return self._policies.get(None)

    def check_job(self, job_name: str, since: Optional[datetime] = None) -> List[TimeoutViolation]:
        """Return violations for a single job within the lookback window."""
        policy = self._policy_for(job_name)
        if policy is None:
            return []

        if since is None:
            since = datetime.utcnow() - timedelta(hours=24)

        records = self._history.get_records(job_name, since=since)
        violations = []
        for record in records:
            if record.duration_seconds is not None and record.duration_seconds > policy.max_duration_seconds:
                violations.append(
                    TimeoutViolation(
                        job_name=job_name,
                        started_at=record.started_at,
                        duration_seconds=record.duration_seconds,
                        max_duration_seconds=policy.max_duration_seconds,
                    )
                )
        return violations

    def check_all(self, job_names: List[str], since: Optional[datetime] = None) -> List[TimeoutViolation]:
        """Return all violations across the provided job names."""
        all_violations: List[TimeoutViolation] = []
        for name in job_names:
            all_violations.extend(self.check_job(name, since=since))
        return all_violations
