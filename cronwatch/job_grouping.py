"""Group jobs by label/tag and provide aggregate status views."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class JobGroup:
    name: str
    job_names: List[str] = field(default_factory=list)

    def add(self, job_name: str) -> None:
        if job_name not in self.job_names:
            self.job_names.append(job_name)

    def remove(self, job_name: str) -> None:
        self.job_names = [j for j in self.job_names if j != job_name]

    def __len__(self) -> int:
        return len(self.job_names)

    def __contains__(self, job_name: str) -> bool:
        return job_name in self.job_names


@dataclass
class GroupStatus:
    group_name: str
    total: int
    healthy: int
    failing: int

    @property
    def all_healthy(self) -> bool:
        return self.failing == 0

    @property
    def health_ratio(self) -> float:
        if self.total == 0:
            return 1.0
        return self.healthy / self.total


class JobGroupManager:
    def __init__(self) -> None:
        self._groups: Dict[str, JobGroup] = {}

    def create_group(self, name: str) -> JobGroup:
        if name not in self._groups:
            self._groups[name] = JobGroup(name=name)
        return self._groups[name]

    def add_job(self, group_name: str, job_name: str) -> None:
        self.create_group(group_name).add(job_name)

    def remove_job(self, group_name: str, job_name: str) -> None:
        if group_name in self._groups:
            self._groups[group_name].remove(job_name)

    def get_group(self, name: str) -> Optional[JobGroup]:
        return self._groups.get(name)

    def groups_for_job(self, job_name: str) -> List[str]:
        return [name for name, grp in self._groups.items() if job_name in grp]

    def all_groups(self) -> List[str]:
        return list(self._groups.keys())

    def status(self, group_name: str, failing_jobs: List[str]) -> Optional[GroupStatus]:
        grp = self._groups.get(group_name)
        if grp is None:
            return None
        failing = [j for j in grp.job_names if j in failing_jobs]
        healthy = len(grp) - len(failing)
        return GroupStatus(
            group_name=group_name,
            total=len(grp),
            healthy=healthy,
            failing=len(failing),
        )
