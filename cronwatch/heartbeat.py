"""Heartbeat tracker for cron jobs — records pings and detects silence."""

import time
from dataclasses import dataclass, field
from typing import Optional

from cronwatch.state import StateStore


@dataclass
class HeartbeatRecord:
    job_name: str
    last_ping: float
    expected_interval: int  # seconds
    missed_count: int = 0


class HeartbeatTracker:
    """Tracks job heartbeats and flags jobs that have gone silent."""

    def __init__(self, store: StateStore, tolerance: float = 1.2):
        self._store = store
        self._tolerance = tolerance  # multiplier over expected interval
        self._records: dict[str, HeartbeatRecord] = {}

    def ping(self, job_name: str, expected_interval: int) -> None:
        """Record a heartbeat ping for a job."""
        now = time.time()
        record = HeartbeatRecord(
            job_name=job_name,
            last_ping=now,
            expected_interval=expected_interval,
            missed_count=0,
        )
        self._records[job_name] = record
        self._store.update_last_run(job_name, now)

    def is_silent(self, job_name: str) -> bool:
        """Return True if the job has not pinged within the expected window."""
        record = self._records.get(job_name)
        if record is None:
            last = self._store.get_last_run(job_name)
            if last is None:
                return False  # never ran, scheduler handles this
            deadline = last + record.expected_interval * self._tolerance if record else None
            return deadline is not None and time.time() > deadline
        deadline = record.last_ping + record.expected_interval * self._tolerance
        return time.time() > deadline

    def get_record(self, job_name: str) -> Optional[HeartbeatRecord]:
        return self._records.get(job_name)

    def increment_missed(self, job_name: str) -> int:
        """Bump missed count and return new value."""
        record = self._records.get(job_name)
        if record is None:
            return 0
        record.missed_count += 1
        return record.missed_count

    def reset(self, job_name: str) -> None:
        """Clear tracking state for a job."""
        self._records.pop(job_name, None)
