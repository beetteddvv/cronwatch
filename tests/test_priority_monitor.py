"""Tests for cronwatch.priority_monitor."""
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.alerts import AlertEvent, AlertManager
from cronwatch.job_priority import Priority, PriorityManager
from cronwatch.priority_monitor import PriorityMonitor


@pytest.fixture
def priority_manager():
    pm = PriorityManager()
    pm.set_priority("critical_job", Priority.CRITICAL)
    pm.set_priority("low_job", Priority.LOW)
    return pm


def _make_event(name: str) -> AlertEvent:
    return AlertEvent(job_name=name, message="missed run", details={})


def _make_monitor(*job_names):
    inner = MagicMock()
    inner.check_all.return_value = [_make_event(n) for n in job_names]
    return inner


def test_check_all_sends_high_priority_events(priority_manager):
    inner = _make_monitor("critical_job")
    am = MagicMock(spec=AlertManager)
    pm = PriorityMonitor(inner, priority_manager, am, min_priority=Priority.NORMAL)
    pm.check_all()
    am.send.assert_called_once()
    sent_event = am.send.call_args[0][0]
    assert "CRITICAL" in sent_event.message


def test_check_all_suppresses_below_min_priority(priority_manager):
    inner = _make_monitor("low_job")
    am = MagicMock(spec=AlertManager)
    pm = PriorityMonitor(inner, priority_manager, am, min_priority=Priority.NORMAL)
    pm.check_all()
    am.send.assert_not_called()
    assert "low_job" in pm.suppressed_jobs


def test_suppressed_count_reflects_suppressed_jobs(priority_manager):
    inner = _make_monitor("low_job", "critical_job")
    am = MagicMock(spec=AlertManager)
    pm = PriorityMonitor(inner, priority_manager, am, min_priority=Priority.NORMAL)
    pm.check_all()
    assert pm.suppressed_count == 1


def test_suppressed_jobs_cleared_between_runs(priority_manager):
    inner = MagicMock()
    inner.check_all.side_effect = [
        [_make_event("low_job")],
        [],
    ]
    am = MagicMock(spec=AlertManager)
    pm = PriorityMonitor(inner, priority_manager, am, min_priority=Priority.NORMAL)
    pm.check_all()
    assert pm.suppressed_count == 1
    pm.check_all()
    assert pm.suppressed_count == 0


def test_check_all_handles_none_return_from_inner(priority_manager):
    inner = MagicMock()
    inner.check_all.return_value = None
    am = MagicMock(spec=AlertManager)
    pm = PriorityMonitor(inner, priority_manager, am)
    pm.check_all()  # should not raise
    am.send.assert_not_called()
