"""Route alerts to different dispatchers based on job labels."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from cronwatch.alerts import AlertEvent
from cronwatch.dispatch import Dispatcher


@dataclass
class RoutingRule:
    """Maps a label key/value pair to a named dispatcher target."""
    label_key: str
    label_value: str
    target: str


class LabelRouter:
    """Routes AlertEvents to dispatchers based on job labels.

    Jobs can carry arbitrary labels (e.g. team='ops', env='prod').  This
    router inspects those labels and forwards the event to the matching
    Dispatcher.  If no rule matches, the event is sent to the default
    dispatcher (if one is registered).
    """

    def __init__(
        self,
        rules: List[RoutingRule],
        dispatchers: Dict[str, Dispatcher],
        default_target: Optional[str] = None,
    ) -> None:
        self._rules = rules
        self._dispatchers = dispatchers
        self._default_target = default_target
        self._unrouted_count = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def route(self, event: AlertEvent, labels: Optional[Dict[str, str]] = None) -> bool:
        """Dispatch *event* to the first matching dispatcher.

        Returns True if a dispatcher handled the event, False otherwise.
        """
        labels = labels or {}
        target = self._resolve_target(labels)

        if target is None:
            self._unrouted_count += 1
            return False

        dispatcher = self._dispatchers.get(target)
        if dispatcher is None:
            self._unrouted_count += 1
            return False

        dispatcher.dispatch(event)
        return True

    @property
    def unrouted_count(self) -> int:
        """Number of events that could not be routed."""
        return self._unrouted_count

    def registered_targets(self) -> List[str]:
        """Return the names of all registered dispatcher targets."""
        return list(self._dispatchers.keys())

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _resolve_target(self, labels: Dict[str, str]) -> Optional[str]:
        for rule in self._rules:
            if labels.get(rule.label_key) == rule.label_value:
                return rule.target
        return self._default_target
