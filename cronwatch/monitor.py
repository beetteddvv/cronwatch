import logging
import time
from datetime import datetime, timezone
from typing import Optional

from cronwatch.alerts import AlertEvent, AlertManager
from cronwatch.config import CronwatchConfig, JobConfig
from cronwatch.scheduler import ScheduleChecker
from cronwatch.state import StateStore

logger = logging.getLogger(__name__)


class Monitor:
    """Main monitoring loop — checks each configured job and fires alerts."""

    def __init__(self, config: CronwatchConfig, state_store: Optional[StateStore] = None):
        self.config = config
        self.store = state_store or StateStore(config.state_file)
        self.alert_manager = AlertManager(config.alerts)

    def check_all(self) -> None:
        """Run a single check pass over all configured jobs."""
        now = datetime.now(tz=timezone.utc)
        for job in self.config.jobs:
            self._check_job(job, now)

    def _check_job(self, job: JobConfig, now: datetime) -> None:
        checker = ScheduleChecker(job)
        last_run = self.store.get_last_run(job.name)

        if checker.is_overdue(last_run, now):
            expected = checker.get_expected_runs(last_run or now, now)
            missed_count = len(expected)
            msg = (
                f"Job has not run since {last_run.isoformat() if last_run else 'never'}; "
                f"{missed_count} expected run(s) missed."
            )
            logger.warning("Missed job detected: %s — %s", job.name, msg)
            self.alert_manager.send(
                AlertEvent(
                    job_name=job.name,
                    event_type="missed",
                    message=msg,
                )
            )

    def record_failure(self, job_name: str, exit_code: int, output: str = "") -> None:
        """Called externally when a job exits with a non-zero code."""
        now = datetime.now(tz=timezone.utc)
        self.store.record_run(job_name, now, success=False)
        msg = output.strip() or f"Exited with code {exit_code}"
        self.alert_manager.send(
            AlertEvent(
                job_name=job_name,
                event_type="failure",
                message=msg,
                exit_code=exit_code,
            )
        )

    def run_forever(self, interval: int = 60) -> None:
        """Block and poll every *interval* seconds."""
        logger.info("cronwatch monitor started (interval=%ds)", interval)
        while True:
            try:
                self.check_all()
            except Exception as exc:
                logger.error("Unexpected error during check: %s", exc)
            time.sleep(interval)
