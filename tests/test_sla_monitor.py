"""Tests for cronwatch/sla_monitor.py"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, call

import pytest

from cronwatch.job_sla import SLAManager, SLARule
from cronwatch.sla_monitor import SLAMonitor


def _now():
    return datetime(2024, 6, 1, 8, 0, 0)


@pytest.fixture
def sla_manager():
    m = SLAManager()
    m.add_rule(SLARule(job_name="report", max_duration_seconds=30, warn_at_percent=0.8))
    return m


@pytest.fixture
def mock_alert_manager():
    return MagicMock()


@pytest.fixture
def monitor(sla_manager, mock_alert_manager):
    return SLAMonitor(sla_manager=sla_manager, alert_manager=mock_alert_manager)


def test_check_all_no_violations_when_within_sla(monitor, mock_alert_manager):
    monitor.start_job("report", at=_now())
    monitor.check_all(at=_now() + timedelta(seconds=10))
    mock_alert_manager.send.assert_not_called()
    assert monitor.violation_count == 0


def test_check_all_sends_warning_alert(monitor, mock_alert_manager):
    monitor.start_job("report", at=_now())
    monitor.check_all(at=_now() + timedelta(seconds=25))  # 25 >= 24 (80% of 30)
    mock_alert_manager.send.assert_called_once()
    event = mock_alert_manager.send.call_args[0][0]
    assert event.job_name == "report"
    assert event.level == "warning"


def test_check_all_sends_critical_alert_on_breach(monitor, mock_alert_manager):
    monitor.start_job("report", at=_now())
    monitor.check_all(at=_now() + timedelta(seconds=35))
    mock_alert_manager.send.assert_called_once()
    event = mock_alert_manager.send.call_args[0][0]
    assert event.level == "critical"


def test_violations_list_populated(monitor):
    monitor.start_job("report", at=_now())
    monitor.check_all(at=_now() + timedelta(seconds=35))
    assert len(monitor.violations) == 1
    assert monitor.violations[0].job_name == "report"


def test_violations_cleared_on_each_check_all(monitor):
    monitor.start_job("report", at=_now())
    monitor.check_all(at=_now() + timedelta(seconds=35))
    assert monitor.violation_count == 1
    # After completing, no active jobs → violations cleared on next check
    monitor.complete_job("report")
    monitor.check_all(at=_now() + timedelta(seconds=40))
    assert monitor.violation_count == 0


def test_complete_job_removes_from_active(monitor):
    monitor.start_job("report", at=_now())
    monitor.complete_job("report")
    monitor.check_all(at=_now() + timedelta(seconds=100))
    assert monitor.violation_count == 0
