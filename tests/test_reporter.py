"""Tests for the Reporter module."""

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

import pytest

from cronwatch.reporter import Reporter, Report, JobStatus
from cronwatch.config import JobConfig, CronwatchConfig, AlertConfig


@pytest.fixture
def alert_config():
    return AlertConfig(method="log")


@pytest.fixture
def base_config(alert_config):
    jobs = [
        JobConfig(name="backup", schedule="0 2 * * *", grace_period=300),
        JobConfig(name="cleanup", schedule="*/5 * * * *", grace_period=60),
    ]
    return CronwatchConfig(jobs=jobs, alert=alert_config)


@pytest.fixture
def mock_store():
    store = MagicMock()
    store.get_failure_count.return_value = 0
    store.get_last_error.return_value = None
    return store


def test_build_report_returns_report_type(base_config, mock_store):
    now = datetime.now(tz=timezone.utc)
    mock_store.get_last_run.return_value = now - timedelta(minutes=1)
    reporter = Reporter(base_config, mock_store)
    report = reporter.build_report()
    assert isinstance(report, Report)


def test_build_report_total_jobs(base_config, mock_store):
    mock_store.get_last_run.return_value = datetime.now(tz=timezone.utc)
    reporter = Reporter(base_config, mock_store)
    report = reporter.build_report()
    assert report.total_jobs == 2


def test_build_report_overdue_count(base_config, mock_store):
    # Return None so both jobs appear overdue
    mock_store.get_last_run.return_value = None
    reporter = Reporter(base_config, mock_store)
    report = reporter.build_report()
    assert report.overdue == 2
    assert report.healthy == 0


def test_build_report_healthy_when_recent(base_config, mock_store):
    now = datetime.now(tz=timezone.utc)
    # Recent run — within grace period for both
    mock_store.get_last_run.return_value = now - timedelta(seconds=10)
    reporter = Reporter(base_config, mock_store)
    report = reporter.build_report()
    assert report.healthy == 2
    assert report.overdue == 0


def test_build_report_failed_count(base_config, mock_store):
    now = datetime.now(tz=timezone.utc)
    mock_store.get_last_run.return_value = now - timedelta(seconds=10)
    mock_store.get_failure_count.return_value = 3
    reporter = Reporter(base_config, mock_store)
    report = reporter.build_report()
    assert report.failed == 2


def test_summary_line_format(base_config, mock_store):
    mock_store.get_last_run.return_value = None
    reporter = Reporter(base_config, mock_store)
    report = reporter.build_report()
    line = report.summary_line
    assert "Jobs:" in line
    assert "healthy" in line
    assert "overdue" in line
    assert "failed" in line


def test_job_status_fields(base_config, mock_store):
    mock_store.get_last_run.return_value = None
    mock_store.get_last_error.return_value = "timeout"
    mock_store.get_failure_count.return_value = 1
    reporter = Reporter(base_config, mock_store)
    report = reporter.build_report()
    status = report.job_statuses[0]
    assert isinstance(status, JobStatus)
    assert status.name == "backup"
    assert status.failure_count == 1
    assert status.last_error == "timeout"
