import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

from cronwatch.monitor import Monitor
from cronwatch.config import CronwatchConfig, JobConfig, AlertConfig


@pytest.fixture
def base_config():
    job = JobConfig(name="nightly", schedule="0 2 * * *", command="/usr/bin/backup.sh")
    alerts = AlertConfig(method="log", recipients=[])
    return CronwatchConfig(jobs=[job], alerts=alerts, state_file="/tmp/cronwatch_test.json")


@pytest.fixture
def mock_store():
    store = MagicMock()
    store.get_last_run.return_value = None
    return store


def test_check_all_calls_get_last_run(base_config, mock_store):
    monitor = Monitor(base_config, state_store=mock_store)
    monitor.check_all()
    mock_store.get_last_run.assert_called_once_with("nightly")


def test_check_all_sends_alert_when_overdue(base_config, mock_store):
    # last run was 3 days ago — definitely overdue for a daily job
    three_days_ago = datetime.now(tz=timezone.utc) - timedelta(days=3)
    mock_store.get_last_run.return_value = three_days_ago

    monitor = Monitor(base_config, state_store=mock_store)
    monitor.alert_manager = MagicMock()
    monitor.check_all()

    monitor.alert_manager.send.assert_called_once()
    event = monitor.alert_manager.send.call_args[0][0]
    assert event.event_type == "missed"
    assert event.job_name == "nightly"


def test_check_all_no_alert_when_recent(base_config, mock_store):
    # last run was 10 minutes ago — not overdue
    recent = datetime.now(tz=timezone.utc) - timedelta(minutes=10)
    mock_store.get_last_run.return_value = recent

    monitor = Monitor(base_config, state_store=mock_store)
    monitor.alert_manager = MagicMock()
    monitor.check_all()

    monitor.alert_manager.send.assert_not_called()


def test_record_failure_saves_run_and_alerts(base_config, mock_store):
    monitor = Monitor(base_config, state_store=mock_store)
    monitor.alert_manager = MagicMock()

    monitor.record_failure("nightly", exit_code=2, output="disk full")

    mock_store.record_run.assert_called_once()
    _, kwargs = mock_store.record_run.call_args
    assert kwargs["success"] is False

    monitor.alert_manager.send.assert_called_once()
    event = monitor.alert_manager.send.call_args[0][0]
    assert event.event_type == "failure"
    assert event.exit_code == 2
    assert "disk full" in event.message
