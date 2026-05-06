"""Persistent state storage for job run history."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class StateStore:
    def __init__(self, path: str = "/tmp/cronwatch_state.json"):
        self.path = Path(path)
        self._data: dict = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            try:
                with open(self.path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save(self) -> None:
        with open(self.path, "w") as f:
            json.dump(self._data, f, indent=2)

    def get_last_run(self, job_name: str) -> Optional[datetime]:
        entry = self._data.get(job_name, {})
        ts = entry.get("last_run")
        if ts:
            return datetime.fromisoformat(ts)
        return None

    def record_run(self, job_name: str, timestamp: Optional[datetime] = None) -> None:
        if timestamp is None:
            timestamp = datetime.now(tz=timezone.utc)
        if job_name not in self._data:
            self._data[job_name] = {}
        self._data[job_name]["last_run"] = timestamp.isoformat()
        self._data[job_name]["failure_count"] = 0
        self._data[job_name]["last_error"] = None
        self._save()

    def record_failure(self, job_name: str, error: Optional[str] = None) -> None:
        if job_name not in self._data:
            self._data[job_name] = {}
        count = self._data[job_name].get("failure_count", 0)
        self._data[job_name]["failure_count"] = count + 1
        self._data[job_name]["last_error"] = error
        self._save()

    def get_failure_count(self, job_name: str) -> int:
        return self._data.get(job_name, {}).get("failure_count", 0)

    def get_last_error(self, job_name: str) -> Optional[str]:
        return self._data.get(job_name, {}).get("last_error")

    def reset(self, job_name: str) -> None:
        """Clear all stored state for a job, as if it has never been seen."""
        if job_name in self._data:
            del self._data[job_name]
            self._save()

    def all_jobs(self) -> list[str]:
        """Return a list of all job names that have recorded state."""
        return list(self._data.keys())
