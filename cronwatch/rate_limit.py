"""Rate limiting for alert dispatch — prevents alert storms."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List


@dataclass
class RateLimitRule:
    max_alerts: int = 10
    window_seconds: int = 3600


@dataclass
class RateLimitState:
    timestamps: List[datetime] = field(default_factory=list)

    def prune(self, window_seconds: int) -> None:
        cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
        self.timestamps = [t for t in self.timestamps if t >= cutoff]

    def record(self) -> None:
        self.timestamps.append(datetime.utcnow())

    def count(self) -> int:
        return len(self.timestamps)


class RateLimiter:
    """Tracks per-job alert rates and blocks excess alerts within a time window."""

    def __init__(self, rule: RateLimitRule) -> None:
        self.rule = rule
        self._states: Dict[str, RateLimitState] = {}

    def _get_state(self, job_name: str) -> RateLimitState:
        if job_name not in self._states:
            self._states[job_name] = RateLimitState()
        return self._states[job_name]

    def is_allowed(self, job_name: str) -> bool:
        """Return True if an alert for job_name is within the rate limit."""
        state = self._get_state(job_name)
        state.prune(self.rule.window_seconds)
        return state.count() < self.rule.max_alerts

    def record(self, job_name: str) -> None:
        """Record that an alert was sent for job_name."""
        state = self._get_state(job_name)
        state.record()

    def current_count(self, job_name: str) -> int:
        """Return the number of alerts sent in the current window."""
        state = self._get_state(job_name)
        state.prune(self.rule.window_seconds)
        return state.count()

    def reset(self, job_name: str) -> None:
        """Clear rate limit state for a job."""
        self._states.pop(job_name, None)
