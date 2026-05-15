"""Persists lifecycle events to disk for post-mortem inspection."""

import json
from pathlib import Path
from typing import List, Optional

from cronwatch.job_lifecycle import LifecycleEvent, LifecycleState


class LifecycleStore:
    """Append-only store for lifecycle events backed by a JSONL file."""

    def __init__(self, path: str) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text("")

    def record(self, event: LifecycleEvent) -> None:
        with self._path.open("a") as fh:
            fh.write(json.dumps(event.to_dict()) + "\n")

    def read_all(self) -> List[LifecycleEvent]:
        events = []
        for line in self._path.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    events.append(LifecycleEvent.from_dict(json.loads(line)))
                except (KeyError, ValueError):
                    continue
        return events

    def events_for_job(self, job_name: str) -> List[LifecycleEvent]:
        return [e for e in self.read_all() if e.job_name == job_name]

    def last_event_for_job(self, job_name: str) -> Optional[LifecycleEvent]:
        events = self.events_for_job(job_name)
        return events[-1] if events else None

    def events_in_state(self, state: LifecycleState) -> List[LifecycleEvent]:
        return [e for e in self.read_all() if e.state == state]

    def clear(self) -> None:
        self._path.write_text("")
