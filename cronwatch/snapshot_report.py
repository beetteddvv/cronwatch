"""Summarize snapshot trends over a time window."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from statistics import mean

from cronwatch.snapshot import Snapshot, SnapshotStore


@dataclass
class SnapshotTrend:
    window_hours: int
    sample_count: int
    avg_healthy: float
    avg_failing: float
    avg_overdue: float
    peak_overdue: int
    peak_failing: int

    def summary(self) -> str:
        return (
            f"Last {self.window_hours}h ({self.sample_count} samples): "
            f"healthy={self.avg_healthy:.1f} failing={self.avg_failing:.1f} "
            f"overdue={self.avg_overdue:.1f} "
            f"[peak overdue={self.peak_overdue} failing={self.peak_failing}]"
        )


class SnapshotReporter:
    def __init__(self, store: SnapshotStore) -> None:
        self._store = store

    def trend(self, hours: int = 24) -> SnapshotTrend | None:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        samples: list[Snapshot] = self._store.since(since)
        if not samples:
            return None
        return SnapshotTrend(
            window_hours=hours,
            sample_count=len(samples),
            avg_healthy=mean(s.healthy for s in samples),
            avg_failing=mean(s.failing for s in samples),
            avg_overdue=mean(s.overdue for s in samples),
            peak_overdue=max(s.overdue for s in samples),
            peak_failing=max(s.failing for s in samples),
        )
