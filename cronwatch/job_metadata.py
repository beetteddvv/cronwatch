"""Job metadata store — attach arbitrary key/value annotations to jobs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class JobMetadata:
    job_name: str
    annotations: Dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any) -> None:
        self.annotations[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.annotations.get(key, default)

    def remove(self, key: str) -> bool:
        if key in self.annotations:
            del self.annotations[key]
            return True
        return False

    def keys(self) -> List[str]:
        return list(self.annotations.keys())

    def to_dict(self) -> Dict[str, Any]:
        return {"job_name": self.job_name, "annotations": dict(self.annotations)}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobMetadata":
        return cls(
            job_name=data["job_name"],
            annotations=dict(data.get("annotations", {})),
        )


class JobMetadataStore:
    """In-memory store for job metadata, keyed by job name."""

    def __init__(self) -> None:
        self._store: Dict[str, JobMetadata] = {}

    def _get_or_create(self, job_name: str) -> JobMetadata:
        if job_name not in self._store:
            self._store[job_name] = JobMetadata(job_name=job_name)
        return self._store[job_name]

    def annotate(self, job_name: str, key: str, value: Any) -> None:
        self._get_or_create(job_name).set(key, value)

    def get_annotation(self, job_name: str, key: str, default: Any = None) -> Any:
        meta = self._store.get(job_name)
        if meta is None:
            return default
        return meta.get(key, default)

    def get_metadata(self, job_name: str) -> Optional[JobMetadata]:
        return self._store.get(job_name)

    def remove_annotation(self, job_name: str, key: str) -> bool:
        meta = self._store.get(job_name)
        if meta is None:
            return False
        return meta.remove(key)

    def all_jobs(self) -> List[str]:
        return list(self._store.keys())

    def jobs_with_annotation(self, key: str) -> List[str]:
        return [
            name for name, meta in self._store.items() if key in meta.annotations
        ]
