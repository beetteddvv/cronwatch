"""Tag-based filtering for cron jobs — lets you target subsets of jobs by tag."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TagFilter:
    """Represents a filter that matches jobs by one or more tags."""

    include: List[str] = field(default_factory=list)
    exclude: List[str] = field(default_factory=list)

    def matches(self, job_tags: List[str]) -> bool:
        """Return True if job_tags satisfies include/exclude rules."""
        tag_set = set(job_tags)

        if self.exclude and tag_set & set(self.exclude):
            return False

        if self.include and not (tag_set & set(self.include)):
            return False

        return True


class TagFilterManager:
    """Applies a TagFilter to a collection of job configs."""

    def __init__(self, tag_filter: Optional[TagFilter] = None) -> None:
        self._filter = tag_filter or TagFilter()

    def filter_jobs(self, jobs: list) -> list:
        """Return only the jobs whose tags match the current filter.

        Jobs without a 'tags' attribute are treated as having no tags.
        An empty TagFilter passes all jobs through.
        """
        if not self._filter.include and not self._filter.exclude:
            return list(jobs)

        result = []
        for job in jobs:
            tags = getattr(job, "tags", []) or []
            if self._filter.matches(tags):
                result.append(job)
        return result

    def active_filter(self) -> TagFilter:
        return self._filter
