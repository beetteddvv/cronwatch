"""Persistent state tracking for job last-run times."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

STATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


class StateStore:
    """Reads and writes job run state to a JSON file."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._data: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            with self.path.open() as f:
                self._data = json.load(f)
        else:
            self._data = {}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w") as f:
            json.dump(self._data, f, indent=2)

    def get_last_run(self, job_name: str) -> Optional[datetime]:
        """Return the last recorded run time for a job, or None."""
        raw = self._data.get(job_name)
        if raw is None:
            return None
        return datetime.strptime(raw, STATE_TIME_FORMAT)

    def record_run(self, job_name: str, run_time: Optional[datetime] = None) -> None:
        """Record a successful run for a job."""
        ts = run_time or datetime.utcnow()
        self._data[job_name] = ts.strftime(STATE_TIME_FORMAT)
        self._save()

    def all_jobs(self) -> dict[str, datetime]:
        """Return all tracked jobs and their last run times."""
        return {
            name: datetime.strptime(ts, STATE_TIME_FORMAT)
            for name, ts in self._data.items()
        }

    def clear(self, job_name: str) -> None:
        """Remove state for a specific job."""
        self._data.pop(job_name, None)
        self._save()
