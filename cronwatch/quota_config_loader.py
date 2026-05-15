"""Load QuotaManager from CronwatchConfig."""

from __future__ import annotations

from cronwatch.config import CronwatchConfig
from cronwatch.job_quota import QuotaManager, QuotaRule


def quota_manager_from_config(config: CronwatchConfig) -> QuotaManager:
    """Build a QuotaManager from job configs that declare quota settings."""
    manager = QuotaManager()
    for job in config.jobs:
        raw = getattr(job, "quota", None)
        if raw is None:
            continue
        max_runs = raw.get("max_runs")
        window_seconds = raw.get("window_seconds")
        if max_runs is not None and window_seconds is not None:
            rule = QuotaRule(
                max_runs=int(max_runs),
                window_seconds=int(window_seconds),
            )
            manager.set_rule(job.name, rule)
    return manager
