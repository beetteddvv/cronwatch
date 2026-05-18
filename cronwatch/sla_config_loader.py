"""Load SLA rules from CronwatchConfig."""

from cronwatch.job_sla import SLAManager, SLARule


def sla_manager_from_config(config) -> SLAManager:
    """Build an SLAManager from a CronwatchConfig instance.

    Each job may define an ``sla`` block with:
      - max_duration_seconds (int, required)
      - warn_at_percent (float, optional, default 0.8)
    """
    manager = SLAManager()
    for job in config.jobs:
        sla_cfg = getattr(job, "sla", None)
        if sla_cfg is None:
            continue
        rule = SLARule(
            job_name=job.name,
            max_duration_seconds=int(sla_cfg.get("max_duration_seconds", 0)),
            warn_at_percent=float(sla_cfg.get("warn_at_percent", 0.8)),
        )
        if rule.max_duration_seconds > 0:
            manager.add_rule(rule)
    return manager
