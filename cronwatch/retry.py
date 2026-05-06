"""Retry policy tracking for cron jobs that fail and are retried."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class RetryPolicy:
    max_attempts: int = 3
    backoff_seconds: int = 60


@dataclass
class RetryState:
    job_name: str
    attempts: int = 0
    last_attempt: Optional[datetime] = None
    exhausted: bool = False

    def increment(self) -> None:
        self.attempts += 1
        self.last_attempt = datetime.utcnow()

    def reset(self) -> None:
        self.attempts = 0
        self.last_attempt = None
        self.exhausted = False


class RetryManager:
    def __init__(self, policy: RetryPolicy) -> None:
        self.policy = policy
        self._states: dict[str, RetryState] = {}

    def _get_state(self, job_name: str) -> RetryState:
        if job_name not in self._states:
            self._states[job_name] = RetryState(job_name=job_name)
        return self._states[job_name]

    def should_retry(self, job_name: str) -> bool:
        state = self._get_state(job_name)
        if state.exhausted:
            return False
        if state.attempts >= self.policy.max_attempts:
            state.exhausted = True
            return False
        if state.last_attempt is not None:
            wait = timedelta(seconds=self.policy.backoff_seconds * state.attempts)
            if datetime.utcnow() - state.last_attempt < wait:
                return False
        return True

    def record_attempt(self, job_name: str) -> RetryState:
        state = self._get_state(job_name)
        state.increment()
        return state

    def reset(self, job_name: str) -> None:
        self._get_state(job_name).reset()

    def get_state(self, job_name: str) -> RetryState:
        return self._get_state(job_name)
