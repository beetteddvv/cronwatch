"""Silence windows — suppress alerts during planned maintenance or downtime."""

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Optional


@dataclass
class SilenceWindow:
    name: str
    start: time
    end: time
    days: list[int] = field(default_factory=lambda: list(range(7)))  # 0=Mon, 6=Sun
    job_names: Optional[list[str]] = None  # None means all jobs

    def covers(self, job_name: str, dt: Optional[datetime] = None) -> bool:
        """Return True if this window suppresses alerts for the given job at dt."""
        if dt is None:
            dt = datetime.now()
        if dt.weekday() not in self.days:
            return False
        current = dt.time().replace(second=0, microsecond=0)
        if self.start <= self.end:
            in_window = self.start <= current <= self.end
        else:
            # Overnight window e.g. 23:00 – 02:00
            in_window = current >= self.start or current <= self.end
        if not in_window:
            return False
        if self.job_names is None:
            return True
        return job_name in self.job_names


class SilenceManager:
    def __init__(self, windows: Optional[list[SilenceWindow]] = None):
        self.windows: list[SilenceWindow] = windows or []

    def add_window(self, window: SilenceWindow) -> None:
        self.windows.append(window)

    def is_silenced(self, job_name: str, dt: Optional[datetime] = None) -> bool:
        """Return True if any window covers this job at the given time."""
        return any(w.covers(job_name, dt) for w in self.windows)

    def active_windows(self, dt: Optional[datetime] = None) -> list[SilenceWindow]:
        """Return all windows that are currently active (regardless of job)."""
        if dt is None:
            dt = datetime.now()
        return [w for w in self.windows if w.covers("", dt) or
                any(w.covers(j, dt) for j in (w.job_names or [""]))]
