"""Collects a Snapshot from live monitor state."""

from __future__ import annotations

from datetime import datetime, timezone

from cronwatch.config import CronwatchConfig
from cronwatch.scheduler import ScheduleChecker
from cronwatch.state import StateStore
from cronwatch.snapshot import Snapshot, SnapshotStore


class SnapshotCollector:
    def __init__(
        self,
        config: CronwatchConfig,
        state_store: StateStore,
        snapshot_store: SnapshotStore,
    ) -> None:
        self._config = config
        self._state = state_store
        self._snapshots = snapshot_store

    def collect(self) -> Snapshot:
        now = datetime.now(timezone.utc)
        total = len(self._config.jobs)
        healthy = 0
        failing = 0
        overdue = 0

        for job in self._config.jobs:
            last_run = self._state.get_last_run(job.name)
            checker = ScheduleChecker(job)
            if checker.is_overdue(last_run, now):
                overdue += 1
            failure_count = self._state.get_failure_count(job.name)
            if failure_count and failure_count > 0:
                failing += 1
            else:
                healthy += 1

        snap = Snapshot(
            timestamp=now.isoformat(),
            total_jobs=total,
            healthy=healthy,
            failing=failing,
            silenced=0,
            overdue=overdue,
        )
        self._snapshots.record(snap)
        return snap
