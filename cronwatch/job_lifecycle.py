"""Tracks job lifecycle state transitions (pending, running, completed, failed)."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional


class LifecycleState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    UNKNOWN = "unknown"

    @classmethod
    def from_str(cls, value: str) -> "LifecycleState":
        try:
            return cls(value.lower())
        except ValueError:
            return cls.UNKNOWN


@dataclass
class LifecycleEvent:
    job_name: str
    state: LifecycleState
    timestamp: datetime = field(default_factory=datetime.utcnow)
    message: str = ""

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "state": self.state.value,
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LifecycleEvent":
        return cls(
            job_name=data["job_name"],
            state=LifecycleState.from_str(data["state"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            message=data.get("message", ""),
        )


class JobLifecycleTracker:
    """Tracks current lifecycle state for each monitored job."""

    def __init__(self) -> None:
        self._states: Dict[str, LifecycleEvent] = {}

    def transition(self, job_name: str, state: LifecycleState, message: str = "") -> LifecycleEvent:
        event = LifecycleEvent(job_name=job_name, state=state, message=message)
        self._states[job_name] = event
        return event

    def current_state(self, job_name: str) -> LifecycleState:
        event = self._states.get(job_name)
        return event.state if event else LifecycleState.UNKNOWN

    def last_event(self, job_name: str) -> Optional[LifecycleEvent]:
        return self._states.get(job_name)

    def all_states(self) -> Dict[str, LifecycleState]:
        return {name: event.state for name, event in self._states.items()}

    def jobs_in_state(self, state: LifecycleState) -> list:
        return [name for name, s in self.all_states().items() if s == state]

    def reset(self, job_name: str) -> None:
        self._states.pop(job_name, None)
