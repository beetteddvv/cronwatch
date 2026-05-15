"""Reporter that surfaces per-group health summaries."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from cronwatch.job_grouping import GroupStatus, JobGroupManager
from cronwatch.reporter import Reporter


@dataclass
class GroupReport:
    group_name: str
    status: GroupStatus
    failing_jobs: List[str] = field(default_factory=list)

    def summary_line(self) -> str:
        pct = int(self.status.health_ratio * 100)
        flag = "OK" if self.status.all_healthy else "DEGRADED"
        return (
            f"[{flag}] {self.group_name}: "
            f"{self.status.healthy}/{self.status.total} healthy ({pct}%)"
        )


class GroupedReporter:
    """Wraps a Reporter and a JobGroupManager to produce group-level summaries."""

    def __init__(self, reporter: Reporter, group_manager: JobGroupManager) -> None:
        self._reporter = reporter
        self._groups = group_manager

    def build_group_report(self, group_name: str) -> Optional[GroupReport]:
        report = self._reporter.build_report()
        failing = [js.job_name for js in report.jobs if not js.healthy]
        status = self._groups.status(group_name, failing)
        if status is None:
            return None
        failing_in_group = [
            j for j in failing
            if j in (self._groups.get_group(group_name) or [])
        ]
        return GroupReport(
            group_name=group_name,
            status=status,
            failing_jobs=failing_in_group,
        )

    def all_group_reports(self) -> Dict[str, GroupReport]:
        results: Dict[str, GroupReport] = {}
        for name in self._groups.all_groups():
            rpt = self.build_group_report(name)
            if rpt is not None:
                results[name] = rpt
        return results

    def any_degraded(self) -> bool:
        return any(
            not r.status.all_healthy
            for r in self.all_group_reports().values()
        )
