"""Job dependency tracking — ensures jobs run in the correct order."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class DependencyViolation:
    job_name: str
    missing_deps: List[str]

    def __str__(self) -> str:
        deps = ", ".join(self.missing_deps)
        return f"{self.job_name} blocked by unmet deps: {deps}"


class DependencyGraph:
    """Tracks which jobs depend on which other jobs completing successfully."""

    def __init__(self) -> None:
        self._deps: Dict[str, List[str]] = {}

    def register(self, job_name: str, depends_on: Optional[List[str]] = None) -> None:
        self._deps[job_name] = depends_on or []

    def dependencies_for(self, job_name: str) -> List[str]:
        return self._deps.get(job_name, [])

    def all_jobs(self) -> List[str]:
        return list(self._deps.keys())


class DependencyChecker:
    """Checks whether a job's dependencies have been satisfied."""

    def __init__(self, graph: DependencyGraph) -> None:
        self._graph = graph

    def check(self, job_name: str, completed: Set[str]) -> Optional[DependencyViolation]:
        """Return a violation if any dependency is not in *completed*, else None."""
        missing = [
            dep
            for dep in self._graph.dependencies_for(job_name)
            if dep not in completed
        ]
        if missing:
            return DependencyViolation(job_name=job_name, missing_deps=missing)
        return None

    def check_all(self, completed: Set[str]) -> List[DependencyViolation]:
        """Return violations for every registered job whose deps are unmet."""
        violations: List[DependencyViolation] = []
        for job in self._graph.all_jobs():
            result = self.check(job, completed)
            if result is not None:
                violations.append(result)
        return violations

    def ready_jobs(self, completed: Set[str]) -> List[str]:
        """Return jobs whose dependencies are all satisfied."""
        return [
            job
            for job in self._graph.all_jobs()
            if not self._graph.dependencies_for(job)
            or all(dep in completed for dep in self._graph.dependencies_for(job))
        ]
