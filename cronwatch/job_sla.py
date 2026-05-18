"""SLA tracking for cron jobs — detect when jobs breach their expected completion windows."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional


@dataclass
class SLARule:
    job_name: str
    max_duration_seconds: int
    warn_at_percent: float = 0.8  # warn when 80% of SLA window consumed

    @property
    def warn_after_seconds(self) -> float:
        return self.max_duration_seconds * self.warn_at_percent


@dataclass
class SLAViolation:
    job_name: str
    started_at: datetime
    elapsed_seconds: float
    limit_seconds: int
    is_warning: bool = False

    def __str__(self) -> str:
        kind = "WARNING" if self.is_warning else "BREACH"
        return (
            f"SLA {kind}: {self.job_name} ran {self.elapsed_seconds:.1f}s "
            f"(limit {self.limit_seconds}s)"
        )


@dataclass
class SLAState:
    job_name: str
    started_at: Optional[datetime] = None
    warned: bool = False


class SLAManager:
    def __init__(self) -> None:
        self._rules: Dict[str, SLARule] = {}
        self._states: Dict[str, SLAState] = {}

    def add_rule(self, rule: SLARule) -> None:
        self._rules[rule.job_name] = rule

    def start_job(self, job_name: str, at: Optional[datetime] = None) -> None:
        self._states[job_name] = SLAState(
            job_name=job_name,
            started_at=at or datetime.utcnow(),
        )

    def check(self, job_name: str, at: Optional[datetime] = None) -> Optional[SLAViolation]:
        rule = self._rules.get(job_name)
        state = self._states.get(job_name)
        if rule is None or state is None or state.started_at is None:
            return None

        now = at or datetime.utcnow()
        elapsed = (now - state.started_at).total_seconds()

        if elapsed >= rule.max_duration_seconds:
            return SLAViolation(
                job_name=job_name,
                started_at=state.started_at,
                elapsed_seconds=elapsed,
                limit_seconds=rule.max_duration_seconds,
                is_warning=False,
            )
        if elapsed >= rule.warn_after_seconds and not state.warned:
            state.warned = True
            return SLAViolation(
                job_name=job_name,
                started_at=state.started_at,
                elapsed_seconds=elapsed,
                limit_seconds=rule.max_duration_seconds,
                is_warning=True,
            )
        return None

    def complete_job(self, job_name: str) -> None:
        self._states.pop(job_name, None)

    def active_jobs(self) -> list:
        return list(self._states.keys())
