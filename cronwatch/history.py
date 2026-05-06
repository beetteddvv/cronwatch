"""Job run history tracking and retrieval."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import json
import os


@dataclass
class RunRecord:
    job_name: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    success: bool = False
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "exit_code": self.exit_code,
            "success": self.success,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RunRecord":
        return cls(
            job_name=data["job_name"],
            started_at=datetime.fromisoformat(data["started_at"]),
            finished_at=datetime.fromisoformat(data["finished_at"]) if data.get("finished_at") else None,
            exit_code=data.get("exit_code"),
            success=data.get("success", False),
            notes=data.get("notes", ""),
        )


class HistoryStore:
    def __init__(self, path: str = "/tmp/cronwatch_history.json", max_records: int = 500):
        self.path = path
        self.max_records = max_records
        self._records: List[RunRecord] = []
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r") as f:
                raw = json.load(f)
            self._records = [RunRecord.from_dict(r) for r in raw]
        except (json.JSONDecodeError, KeyError):
            self._records = []

    def _save(self) -> None:
        with open(self.path, "w") as f:
            json.dump([r.to_dict() for r in self._records], f, indent=2)

    def append(self, record: RunRecord) -> None:
        self._records.append(record)
        if len(self._records) > self.max_records:
            self._records = self._records[-self.max_records:]
        self._save()

    def get_for_job(self, job_name: str, limit: int = 10) -> List[RunRecord]:
        matches = [r for r in self._records if r.job_name == job_name]
        return matches[-limit:]

    def get_recent_failures(self, job_name: str, limit: int = 5) -> List[RunRecord]:
        matches = [r for r in self._records if r.job_name == job_name and not r.success]
        return matches[-limit:]

    def failure_count(self, job_name: str) -> int:
        return sum(1 for r in self._records if r.job_name == job_name and not r.success)
