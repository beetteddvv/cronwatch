"""Monitor wrapper that applies escalation logic before dispatching alerts."""

from cronwatch.monitor import Monitor
from cronwatch.escalation import EscalationManager, EscalationPolicy
from cronwatch.alerts import AlertEvent
from cronwatch.dispatch import Dispatcher


class EscalationMonitor:
    """Wraps Monitor and upgrades the alert channel when a job keeps failing."""

    def __init__(
        self,
        monitor: Monitor,
        dispatcher: Dispatcher,
        policy: EscalationPolicy,
    ) -> None:
        self.monitor = monitor
        self.dispatcher = dispatcher
        self.escalation = EscalationManager(policy)

    def check_all(self) -> int:
        """Run checks and dispatch alerts with escalation applied.

        Returns the number of alerts dispatched.
        """
        events = self.monitor.check_all()
        dispatched = 0

        for event in events:
            job_name = event.job_name
            triggered = self.escalation.record_failure(job_name)

            channel = self.escalation.channel_for(
                job_name, event.channel or "log"
            )

            upgraded_event = AlertEvent(
                job_name=job_name,
                reason=event.reason,
                channel=channel,
                escalated=self.escalation.is_escalated(job_name),
                triggered_escalation=triggered,
            )

            self.dispatcher.dispatch(upgraded_event)
            dispatched += 1

        return dispatched

    def record_success(self, job_name: str) -> None:
        """Notify escalation manager that a job succeeded."""
        self.escalation.record_success(job_name)
