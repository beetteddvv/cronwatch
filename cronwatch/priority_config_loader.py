"""Load job priority configuration from the main CronwatchConfig."""
from __future__ import annotations

from typing import Any, Dict, List

from cronwatch.config import CronwatchConfig
from cronwatch.job_priority import Priority, PriorityManager, load_priority_rules

_PRIORITY_KEY = "job_priorities"


def priority_manager_from_config(
    config: CronwatchConfig,
    extra: Dict[str, Any] | None = None,
) -> PriorityManager:
    """Build a PriorityManager from a CronwatchConfig.

    Priority can be declared in two ways:
    1. Via an optional ``job_priorities`` list in *extra* (raw config dict).
    2. Via a ``priority`` field on individual JobConfig objects (if present).

    Both sources are merged; explicit list entries take precedence.
    """
    manager = PriorityManager()

    # 1. Per-job priority from JobConfig attributes (optional field)
    for job in config.jobs:
        raw_priority = getattr(job, "priority", None)
        if raw_priority:
            try:
                manager.set_priority(job.name, Priority.from_str(raw_priority))
            except ValueError:
                pass  # ignore unrecognised values; fall back to NORMAL

    # 2. Explicit override list from extra config dict
    if extra:
        rules: List[Dict] = extra.get(_PRIORITY_KEY, [])
        override_manager = load_priority_rules(rules)
        for job_name, priority in override_manager.all_rules().items():
            manager.set_priority(job_name, priority)

    return manager


def min_priority_from_config(
    extra: Dict[str, Any] | None,
    default: Priority = Priority.LOW,
) -> Priority:
    """Return the configured minimum dispatch priority, or *default*."""
    if not extra:
        return default
    raw = extra.get("min_alert_priority")
    if raw is None:
        return default
    try:
        return Priority.from_str(str(raw))
    except ValueError:
        return default
