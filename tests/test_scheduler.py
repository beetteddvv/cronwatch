"""Tests for cronwatch.scheduler."""

from datetime import datetime, timedelta

import pytest

from cronwatch.config import JobConfig
from cronwatch.scheduler import ScheduleChecker


@pytest.fixture
def every_minute_job():
    return JobConfig(name="heartbeat", schedule="* * * * *", command="echo ok")


@pytest.fixture
def hourly_job():
    return JobConfig(name="hourly", schedule="0 * * * *", command="echo hourly")


def test_get_expected_runs_returns_correct_count(every_minute_job):
    checker = ScheduleChecker(every_minute_job)
    since = datetime(2024, 1, 1, 12, 0, 0)
    until = datetime(2024, 1, 1, 12, 5, 0)
    runs = checker.get_expected_runs(since, until)
    assert len(runs) == 5


def test_get_expected_runs_empty_when_no_runs(hourly_job):
    checker = ScheduleChecker(hourly_job)
    since = datetime(2024, 1, 1, 12, 1, 0)
    until = datetime(2024, 1, 1, 12, 59, 0)
    runs = checker.get_expected_runs(since, until)
    assert runs == []


def test_is_overdue_true_when_missed(every_minute_job):
    checker = ScheduleChecker(every_minute_job)
    last_run = datetime(2024, 1, 1, 12, 0, 0)
    now = datetime(2024, 1, 1, 12, 3, 0)
    assert checker.is_overdue(last_run, now=now) is True


def test_is_overdue_false_when_recent(every_minute_job):
    checker = ScheduleChecker(every_minute_job)
    now = datetime(2024, 1, 1, 12, 3, 45)
    last_run = datetime(2024, 1, 1, 12, 3, 0)
    assert checker.is_overdue(last_run, now=now) is False


def test_is_overdue_none_last_run(every_minute_job):
    checker = ScheduleChecker(every_minute_job)
    now = datetime(2024, 1, 1, 12, 5, 0)
    # Never ran, should be overdue
    assert checker.is_overdue(None, now=now) is True


def test_next_run_is_in_future(hourly_job):
    checker = ScheduleChecker(hourly_job)
    after = datetime(2024, 1, 1, 12, 30, 0)
    nxt = checker.next_run(after=after)
    assert nxt > after
    assert nxt == datetime(2024, 1, 1, 13, 0, 0)


def test_invalid_schedule_raises():
    job = JobConfig(name="bad", schedule="not-a-cron", command="echo x")
    checker = ScheduleChecker(job)
    with pytest.raises(ValueError, match="Invalid cron expression"):
        checker.get_expected_runs(datetime.utcnow(), datetime.utcnow())
