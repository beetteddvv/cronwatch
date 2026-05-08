"""Cron schedule parsing and missed run detection."""

from datetime import datetime, timedelta
from typing import Optional

from croniter import croniter

from cronwatch.config import JobConfig


class ScheduleChecker:
    """Checks whether a cron job has missed its expected runs."""

    def __init__(self, job: JobConfig):
        self.job = job

    def get_expected_runs(self, since: datetime, until: datetime) -> list[datetime]:
        """Return all expected run times between since and until."""
        if not croniter.is_valid(self.job.schedule):
            raise ValueError(f"Invalid cron expression for job '{self.job.name}': {self.job.schedule}")

        cron = croniter(self.job.schedule, since - timedelta(seconds=1))
        runs = []
        while True:
            next_run = cron.get_next(datetime)
            if next_run >= until:
                break
            runs.append(next_run)
        return runs

    def is_overdue(self, last_run: Optional[datetime], now: Optional[datetime] = None) -> bool:
        """Return True if the job has missed at least one expected run."""
        now = now or datetime.utcnow()
        if last_run is None:
            # Never ran — check if it should have by now
            cron = croniter(self.job.schedule, now - timedelta(days=1))
            first_expected = cron.get_next(datetime)
            return first_expected <= now

        missed = self.get_expected_runs(since=last_run, until=now)
        return len(missed) > 0

    def missed_run_count(self, last_run: Optional[datetime], now: Optional[datetime] = None) -> int:
        """Return the number of expected runs missed since last_run.

        If last_run is None, counts missed runs over the past day.
        """
        now = now or datetime.utcnow()
        if last_run is None:
            since = now - timedelta(days=1)
        else:
            since = last_run
        return len(self.get_expected_runs(since=since, until=now))

    def next_run(self, after: Optional[datetime] = None) -> datetime:
        """Return the next scheduled run time."""
        after = after or datetime.utcnow()
        cron = croniter(self.job.schedule, after)
        return cron.get_next(datetime)
