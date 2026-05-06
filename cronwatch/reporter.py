"""Generate summary reports of cron job health and history."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from cronwatch.config import CronwatchConfig
from cronwatch.state import StateStore
from cronwatch.scheduler import ScheduleChecker


@dataclass
class JobStatus:
    name: str
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    is_overdue: bool
    failure_count: int
    last_error: Optional[str] = None


@dataclass
class Report:
    generated_at: datetime
    total_jobs: int
    healthy: int
    overdue: int
    failed: int
    job_statuses: list = field(default_factory=list)

    @property
    def summary_line(self) -> str:
        return (
            f"[{self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}] "
            f"Jobs: {self.total_jobs} total, "
            f"{self.healthy} healthy, "
            f"{self.overdue} overdue, "
            f"{self.failed} failed"
        )


class Reporter:
    def __init__(self, config: CronwatchConfig, store: StateStore):
        self.config = config
        self.store = store

    def build_report(self) -> Report:
        now = datetime.now(tz=timezone.utc)
        statuses = []

        for job in self.config.jobs:
            checker = ScheduleChecker(job, now)
            last_run = self.store.get_last_run(job.name)
            overdue = checker.is_overdue(last_run)
            failure_count = self.store.get_failure_count(job.name)
            last_error = self.store.get_last_error(job.name)

            statuses.append(JobStatus(
                name=job.name,
                last_run=last_run,
                next_run=checker.next_run(),
                is_overdue=overdue,
                failure_count=failure_count,
                last_error=last_error,
            ))

        overdue_jobs = [s for s in statuses if s.is_overdue]
        failed_jobs = [s for s in statuses if s.failure_count > 0]
        healthy_jobs = [s for s in statuses if not s.is_overdue and s.failure_count == 0]

        return Report(
            generated_at=now,
            total_jobs=len(statuses),
            healthy=len(healthy_jobs),
            overdue=len(overdue_jobs),
            failed=len(failed_jobs),
            job_statuses=statuses,
        )
