"""Load job ownership configuration from the CronwatchConfig jobs list."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cronwatch.job_ownership import OwnerRecord, OwnershipRegistry

if TYPE_CHECKING:
    from cronwatch.config import CronwatchConfig


def ownership_registry_from_config(config: "CronwatchConfig") -> OwnershipRegistry:
    """Build an OwnershipRegistry from job metadata in the config.

    Each job may carry optional ``owner``, ``team``, and ``contact`` fields.
    Jobs that omit all three are simply not registered.
    """
    registry = OwnershipRegistry()

    for job in config.jobs:
        owner = getattr(job, "owner", None)
        team = getattr(job, "team", None)
        contact = getattr(job, "contact", None)

        if owner or team or contact:
            registry.register(
                OwnerRecord(
                    job_name=job.name,
                    owner=owner or "unknown",
                    team=team,
                    contact=contact,
                )
            )

    return registry
