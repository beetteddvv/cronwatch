"""Job priority levels and priority-aware alert routing."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, List, Optional


class Priority(IntEnum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

    @classmethod
    def from_str(cls, value: str) -> "Priority":
        mapping = {
            "low": cls.LOW,
            "normal": cls.NORMAL,
            "high": cls.HIGH,
            "critical": cls.CRITICAL,
        }
        key = value.strip().lower()
        if key not in mapping:
            raise ValueError(f"Unknown priority: {value!r}")
        return mapping[key]


@dataclass
class PriorityRule:
    job_name: str
    priority: Priority


@dataclass
class PriorityManager:
    _rules: Dict[str, Priority] = field(default_factory=dict)

    def set_priority(self, job_name: str, priority: Priority) -> None:
        self._rules[job_name] = priority

    def get_priority(self, job_name: str) -> Priority:
        return self._rules.get(job_name, Priority.NORMAL)

    def jobs_at_or_above(self, threshold: Priority) -> List[str]:
        return [
            name for name, pri in self._rules.items() if pri >= threshold
        ]

    def all_rules(self) -> Dict[str, Priority]:
        return dict(self._rules)


def load_priority_rules(raw: List[Dict]) -> PriorityManager:
    """Build a PriorityManager from a list of config dicts."""
    manager = PriorityManager()
    for entry in raw:
        name = entry["job"]
        priority = Priority.from_str(entry.get("priority", "normal"))
        manager.set_priority(name, priority)
    return manager
