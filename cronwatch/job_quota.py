"""Job execution quota tracking — enforce max run counts per time window."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List


@dataclass
class QuotaRule:
    max_runs: int
    window_seconds: int  # rolling window size

    @property
    def window(self) -> timedelta:
        return timedelta(seconds=self.window_seconds)


@dataclass
class QuotaState:
    job_name: str
    run_times: List[datetime] = field(default_factory=list)

    def prune(self, window: timedelta, now: datetime) -> None:
        cutoff = now - window
        self.run_times = [t for t in self.run_times if t >= cutoff]

    def record(self, now: datetime) -> None:
        self.run_times.append(now)

    def count(self) -> int:
        return len(self.run_times)


class QuotaManager:
    def __init__(self) -> None:
        self._rules: Dict[str, QuotaRule] = {}
        self._states: Dict[str, QuotaState] = {}

    def set_rule(self, job_name: str, rule: QuotaRule) -> None:
        self._rules[job_name] = rule

    def _get_state(self, job_name: str) -> QuotaState:
        if job_name not in self._states:
            self._states[job_name] = QuotaState(job_name=job_name)
        return self._states[job_name]

    def record_run(self, job_name: str, now: datetime | None = None) -> None:
        now = now or datetime.utcnow()
        rule = self._rules.get(job_name)
        state = self._get_state(job_name)
        if rule:
            state.prune(rule.window, now)
        state.record(now)

    def is_over_quota(self, job_name: str, now: datetime | None = None) -> bool:
        now = now or datetime.utcnow()
        rule = self._rules.get(job_name)
        if rule is None:
            return False
        state = self._get_state(job_name)
        state.prune(rule.window, now)
        return state.count() > rule.max_runs

    def run_count(self, job_name: str, now: datetime | None = None) -> int:
        now = now or datetime.utcnow()
        rule = self._rules.get(job_name)
        state = self._get_state(job_name)
        if rule:
            state.prune(rule.window, now)
        return state.count()
