"""Alert escalation: upgrade alert severity after repeated failures."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


@dataclass
class EscalationPolicy:
    threshold: int = 3          # failures before escalating
    escalated_channel: str = "email"  # channel to use after escalation
    reset_on_success: bool = True


@dataclass
class EscalationState:
    job_name: str
    failure_count: int = 0
    escalated: bool = False
    last_escalated_at: Optional[datetime] = None


class EscalationManager:
    def __init__(self, policy: EscalationPolicy) -> None:
        self.policy = policy
        self._states: Dict[str, EscalationState] = {}

    def _get_state(self, job_name: str) -> EscalationState:
        if job_name not in self._states:
            self._states[job_name] = EscalationState(job_name=job_name)
        return self._states[job_name]

    def record_failure(self, job_name: str) -> bool:
        """Record a failure. Returns True if this failure triggers escalation."""
        state = self._get_state(job_name)
        state.failure_count += 1
        if not state.escalated and state.failure_count >= self.policy.threshold:
            state.escalated = True
            state.last_escalated_at = datetime.utcnow()
            return True
        return False

    def record_success(self, job_name: str) -> None:
        """Reset escalation state on success if policy allows."""
        if self.policy.reset_on_success:
            self._states.pop(job_name, None)

    def is_escalated(self, job_name: str) -> bool:
        state = self._states.get(job_name)
        return state.escalated if state else False

    def failure_count(self, job_name: str) -> int:
        state = self._states.get(job_name)
        return state.failure_count if state else 0

    def channel_for(self, job_name: str, default_channel: str) -> str:
        """Return the appropriate alert channel given current escalation state."""
        if self.is_escalated(job_name):
            return self.policy.escalated_channel
        return default_channel
