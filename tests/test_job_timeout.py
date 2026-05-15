"""Tests for cronwatch.job_timeout."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from cronwatch.job_timeout import JobTimeoutChecker, TimeoutPolicy, TimeoutViolation
from cronwatch.history import RunRecord


NOW = datetime(2024, 6, 1, 12, 0, 0)


def _record(job_name: str, duration: float, started_at: datetime = NOW) -> RunRecord:
    r = MagicMock(spec=RunRecord)
    r.job_name = job_name
    r.duration_seconds = duration
    r.started_at = started_at
    return r


@pytest.fixture
def history():
    return MagicMock()


@pytest.fixture
def checker(history):
    policies = [
        TimeoutPolicy(max_duration_seconds=60.0, job_name="backup"),
        TimeoutPolicy(max_duration_seconds=30.0, job_name=None),  # default
    ]
    return JobTimeoutChecker(history, policies)


def test_check_job_no_violation_within_limit(checker, history):
    history.get_records.return_value = [_record("backup", 45.0)]
    violations = checker.check_job("backup", since=NOW - timedelta(hours=1))
    assert violations == []


def test_check_job_returns_violation_when_exceeded(checker, history):
    history.get_records.return_value = [_record("backup", 120.0)]
    violations = checker.check_job("backup", since=NOW - timedelta(hours=1))
    assert len(violations) == 1
    assert violations[0].job_name == "backup"
    assert violations[0].duration_seconds == 120.0
    assert violations[0].max_duration_seconds == 60.0


def test_check_job_uses_default_policy_for_unknown_job(checker, history):
    history.get_records.return_value = [_record("cleanup", 50.0)]
    violations = checker.check_job("cleanup", since=NOW - timedelta(hours=1))
    assert len(violations) == 1
    assert violations[0].max_duration_seconds == 30.0


def test_check_job_no_policy_returns_empty(history):
    checker = JobTimeoutChecker(history, [])
    history.get_records.return_value = [_record("anything", 9999.0)]
    violations = checker.check_job("anything", since=NOW - timedelta(hours=1))
    assert violations == []


def test_check_all_aggregates_violations(checker, history):
    def get_records(job_name, since):
        if job_name == "backup":
            return [_record("backup", 200.0)]
        if job_name == "sync":
            return [_record("sync", 5.0)]
        return []

    history.get_records.side_effect = get_records
    violations = checker.check_all(["backup", "sync"], since=NOW - timedelta(hours=1))
    assert len(violations) == 1
    assert violations[0].job_name == "backup"


def test_violation_str_contains_job_name():
    v = TimeoutViolation(
        job_name="nightly",
        started_at=NOW,
        duration_seconds=90.0,
        max_duration_seconds=60.0,
    )
    assert "nightly" in str(v)
    assert "90.0" in str(v)
    assert "60.0" in str(v)


def test_check_job_skips_records_with_none_duration(checker, history):
    r = _record("backup", 0)
    r.duration_seconds = None
    history.get_records.return_value = [r]
    violations = checker.check_job("backup", since=NOW - timedelta(hours=1))
    assert violations == []
