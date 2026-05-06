"""Alert throttling to prevent notification floods."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional


@dataclass
class ThrottleRule:
    min_interval_seconds: int = 300  # 5 minutes default
    max_alerts_per_hour: int = 10


@dataclass
class ThrottleState:
    last_sent: Optional[datetime] = None
    count_this_hour: int = 0
    hour_window_start: Optional[datetime] = None


class AlertThrottle:
    """Tracks alert send history and decides whether to suppress."""

    def __init__(self, rule: Optional[ThrottleRule] = None):
        self.rule = rule or ThrottleRule()
        self._state: Dict[str, ThrottleState] = {}

    def _get_state(self, key: str) -> ThrottleState:
        if key not in self._state:
            self._state[key] = ThrottleState()
        return self._state[key]

    def should_send(self, job_name: str, now: Optional[datetime] = None) -> bool:
        """Return True if alert should be sent, False if throttled."""
        now = now or datetime.utcnow()
        state = self._get_state(job_name)

        # Check minimum interval between alerts
        if state.last_sent is not None:
            elapsed = (now - state.last_sent).total_seconds()
            if elapsed < self.rule.min_interval_seconds:
                return False

        # Check hourly cap
        if state.hour_window_start is None or (
            now - state.hour_window_start
        ) >= timedelta(hours=1):
            state.hour_window_start = now
            state.count_this_hour = 0

        if state.count_this_hour >= self.rule.max_alerts_per_hour:
            return False

        return True

    def record_send(self, job_name: str, now: Optional[datetime] = None) -> None:
        """Mark that an alert was sent for the given job."""
        now = now or datetime.utcnow()
        state = self._get_state(job_name)
        state.last_sent = now
        state.count_this_hour = (state.count_this_hour or 0) + 1

    def reset(self, job_name: str) -> None:
        """Clear throttle state for a job (e.g. after successful run)."""
        self._state.pop(job_name, None)
