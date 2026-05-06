"""Generates human-readable summaries from job run history."""

from dataclasses import dataclass
from typing import List
from cronwatch.history import HistoryStore, RunRecord


@dataclass
class JobHistorySummary:
    job_name: str
    total_runs: int
    successful_runs: int
    failed_runs: int
    failure_rate: float
    last_run: RunRecord | None

    @property
    def healthy(self) -> bool:
        return self.failure_rate < 0.1


class HistoryReporter:
    def __init__(self, store: HistoryStore):
        self._store = store

    def summarize(self, job_name: str, limit: int = 50) -> JobHistorySummary:
        records = self._store.get_for_job(job_name, limit=limit)
        total = len(records)
        if total == 0:
            return JobHistorySummary(
                job_name=job_name,
                total_runs=0,
                successful_runs=0,
                failed_runs=0,
                failure_rate=0.0,
                last_run=None,
            )
        successful = sum(1 for r in records if r.success)
        failed = total - successful
        return JobHistorySummary(
            job_name=job_name,
            total_runs=total,
            successful_runs=successful,
            failed_runs=failed,
            failure_rate=failed / total,
            last_run=records[-1],
        )

    def format_summary(self, summary: JobHistorySummary) -> str:
        status = "OK" if summary.healthy else "DEGRADED"
        last = (
            summary.last_run.started_at.strftime("%Y-%m-%d %H:%M:%S")
            if summary.last_run
            else "never"
        )
        return (
            f"[{status}] {summary.job_name}: "
            f"{summary.successful_runs}/{summary.total_runs} successful "
            f"(failure rate {summary.failure_rate:.0%}), last run: {last}"
        )

    def report_all(self, job_names: List[str]) -> List[str]:
        lines = []
        for name in job_names:
            summary = self.summarize(name)
            lines.append(self.format_summary(summary))
        return lines
