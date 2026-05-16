"""Job cooldown enforcement — prevents re-alerting too soon after a job recovers."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional


@dataclass
class CooldownRule:
    job_name: str
    cooldown_seconds: int

    @property
    def cooldown(self) -> timedelta:
        return timedelta(seconds=self.cooldown_seconds)


@dataclass
class CooldownState:
    job_name: str
    recovered_at: Optional[datetime] = None

    def is_cooling_down(self, rule: CooldownRule, now: Optional[datetime] = None) -> bool:
        if self.recovered_at is None:
            return False
        now = now or datetime.utcnow()
        return (now - self.recovered_at) < rule.cooldown

    def mark_recovered(self, now: Optional[datetime] = None) -> None:
        self.recovered_at = now or datetime.utcnow()

    def clear(self) -> None:
        self.recovered_at = None


class CooldownManager:
    def __init__(self) -> None:
        self._rules: Dict[str, CooldownRule] = {}
        self._states: Dict[str, CooldownState] = {}

    def add_rule(self, rule: CooldownRule) -> None:
        self._rules[rule.job_name] = rule

    def _get_state(self, job_name: str) -> CooldownState:
        if job_name not in self._states:
            self._states[job_name] = CooldownState(job_name=job_name)
        return self._states[job_name]

    def mark_recovered(self, job_name: str, now: Optional[datetime] = None) -> None:
        state = self._get_state(job_name)
        state.mark_recovered(now=now)

    def is_cooling_down(self, job_name: str, now: Optional[datetime] = None) -> bool:
        rule = self._rules.get(job_name)
        if rule is None:
            return False
        state = self._get_state(job_name)
        return state.is_cooling_down(rule, now=now)

    def clear(self, job_name: str) -> None:
        state = self._get_state(job_name)
        state.clear()

    def rule_for(self, job_name: str) -> Optional[CooldownRule]:
        return self._rules.get(job_name)
