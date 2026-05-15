"""Job annotation filtering — filter and query jobs by metadata annotations."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from cronwatch.job_metadata import JobMetadata


@dataclass
class AnnotationCriteria:
    """Criteria for matching jobs by annotation key/value."""
    key: str
    value: Optional[Any] = None  # None means: key must exist, any value

    def matches(self, metadata: JobMetadata, job_name: str) -> bool:
        if not metadata.has(job_name, self.key):
            return False
        if self.value is None:
            return True
        return metadata.get(job_name, self.key) == self.value


class AnnotationFilter:
    """Filter a list of job names based on annotation criteria."""

    def __init__(self, metadata: JobMetadata) -> None:
        self._metadata = metadata
        self._criteria: List[AnnotationCriteria] = []

    def add_criterion(self, key: str, value: Optional[Any] = None) -> "AnnotationFilter":
        self._criteria.append(AnnotationCriteria(key=key, value=value))
        return self

    def matches(self, job_name: str) -> bool:
        """Return True if job_name satisfies all criteria."""
        if not self._criteria:
            return True
        return all(c.matches(self._metadata, job_name) for c in self._criteria)

    def apply(self, job_names: List[str]) -> List[str]:
        """Return only the job names that satisfy all criteria."""
        return [j for j in job_names if self.matches(j)]

    def excluded(self, job_names: List[str]) -> List[str]:
        """Return job names that do NOT satisfy all criteria."""
        return [j for j in job_names if not self.matches(j)]


def jobs_with_annotation(metadata: JobMetadata, key: str) -> List[str]:
    """Return all job names that have a given annotation key."""
    return [name for name in metadata.all_jobs() if metadata.has(name, key)]


def jobs_with_annotation_value(
    metadata: JobMetadata, key: str, value: Any
) -> List[str]:
    """Return all job names where annotation key == value."""
    return [
        name for name in metadata.all_jobs()
        if metadata.get(name, key) == value
    ]
