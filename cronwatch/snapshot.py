"""Periodic snapshots of monitor state for trend analysis and diagnostics."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


@dataclass
class Snapshot:
    timestamp: str
    total_jobs: int
    healthy: int
    failing: int
    silenced: int
    overdue: int
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        extra = data.pop("extra", {})
        return cls(**data, extra=extra)


class SnapshotStore:
    def __init__(self, path: str, max_snapshots: int = 500) -> None:
        self.path = path
        self.max_snapshots = max_snapshots
        self._records: list[Snapshot] = []
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.path):
            return
        with open(self.path, "r") as f:
            raw = json.load(f)
        self._records = [Snapshot.from_dict(r) for r in raw]

    def _save(self) -> None:
        with open(self.path, "w") as f:
            json.dump([r.to_dict() for r in self._records], f, indent=2)

    def record(self, snapshot: Snapshot) -> None:
        self._records.append(snapshot)
        if len(self._records) > self.max_snapshots:
            self._records = self._records[-self.max_snapshots :]
        self._save()

    def latest(self) -> Snapshot | None:
        return self._records[-1] if self._records else None

    def all(self) -> list[Snapshot]:
        return list(self._records)

    def since(self, dt: datetime) -> list[Snapshot]:
        cutoff = dt.isoformat()
        return [r for r in self._records if r.timestamp >= cutoff]
