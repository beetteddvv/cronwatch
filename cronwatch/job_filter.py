"""Filter cron jobs by status, schedule pattern, or name prefix."""

from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import List, Optional, Sequence


@dataclass
class JobFilterCriteria:
    """Criteria used to select a subset of jobs."""

    name_pattern: Optional[str] = None  # supports shell-style wildcards
    schedule_contains: Optional[str] = None  # substring match on cron expression
    tags_any: List[str] = field(default_factory=list)  # job must have at least one
    tags_all: List[str] = field(default_factory=list)  # job must have all of these


class JobFilter:
    """Applies a JobFilterCriteria against a sequence of job config objects."""

    def __init__(self, criteria: JobFilterCriteria) -> None:
        self.criteria = criteria

    def matches(self, job) -> bool:
        c = self.criteria

        if c.name_pattern and not fnmatch(job.name, c.name_pattern):
            return False

        if c.schedule_contains and c.schedule_contains not in job.schedule:
            return False

        job_tags = set(getattr(job, "tags", []) or [])

        if c.tags_any and not job_tags.intersection(c.tags_any):
            return False

        if c.tags_all and not set(c.tags_all).issubset(job_tags):
            return False

        return True

    def apply(self, jobs: Sequence) -> List:
        """Return only the jobs that satisfy all criteria."""
        return [j for j in jobs if self.matches(j)]

    def excluded(self, jobs: Sequence) -> List:
        """Return jobs that did NOT match (complement of apply)."""
        return [j for j in jobs if not self.matches(j)]
