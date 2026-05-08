"""Audit log for cronwatch — records all alert dispatches and check events."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import json
import os


@dataclass
class AuditEntry:
    timestamp: str
    event_type: str  # 'alert_sent', 'check_passed', 'check_failed', 'suppressed'
    job_name: str
    detail: str
    method: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "job_name": self.job_name,
            "detail": self.detail,
            "method": self.method,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        return cls(
            timestamp=data["timestamp"],
            event_type=data["event_type"],
            job_name=data["job_name"],
            detail=data["detail"],
            method=data.get("method"),
        )


class AuditLog:
    def __init__(self, path: str = "cronwatch_audit.json"):
        self._path = path
        self._entries: List[AuditEntry] = []
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self._path):
            return
        try:
            with open(self._path, "r") as f:
                raw = json.load(f)
            self._entries = [AuditEntry.from_dict(e) for e in raw]
        except (json.JSONDecodeError, KeyError):
            self._entries = []

    def _save(self) -> None:
        with open(self._path, "w") as f:
            json.dump([e.to_dict() for e in self._entries], f, indent=2)

    def record(self, event_type: str, job_name: str, detail: str, method: Optional[str] = None) -> AuditEntry:
        entry = AuditEntry(
            timestamp=datetime.utcnow().isoformat(),
            event_type=event_type,
            job_name=job_name,
            detail=detail,
            method=method,
        )
        self._entries.append(entry)
        self._save()
        return entry

    def get_entries(self, job_name: Optional[str] = None, event_type: Optional[str] = None) -> List[AuditEntry]:
        results = self._entries
        if job_name:
            results = [e for e in results if e.job_name == job_name]
        if event_type:
            results = [e for e in results if e.event_type == event_type]
        return results

    def clear(self) -> None:
        self._entries = []
        self._save()

    @property
    def entry_count(self) -> int:
        return len(self._entries)
