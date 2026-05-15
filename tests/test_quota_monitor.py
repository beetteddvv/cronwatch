"""Tests for cronwatch.quota_monitor."""

from datetime import datetime
from typing import List
from unittest.mock import MagicMock

import pytest

from cronwatch.alerts import AlertEvent
from cronwatch.job_quota import QuotaManager, QuotaRule
from cronwatch.quota_monitor import QuotaMonitor


NOW = datetime(2024, 1, 1, 12, 0, 0)


def _make_event(job_name: str) -> AlertEvent:
    return AlertEvent(
        job_name=job_name,
        reason="missed",
        timestamp=NOW,
        details={},
    )


def _make_monitor(events: List[AlertEvent]) -> MagicMock:
    inner = MagicMock()
    inner.check_all.return_value = events
    return inner


@pytest.fixture
def quota_manager() -> QuotaManager:
    m = QuotaManager()
    m.set_rule("backup", QuotaRule(max_runs=2, window_seconds=60))
    return m


def test_check_all_passes_events_under_quota(quota_manager: QuotaManager) -> None:
    events = [_make_event("backup"), _make_event("backup")]
    monitor = QuotaMonitor(_make_monitor(events), quota_manager)
    result = monitor.check_all()
    assert len(result) == 2


def test_check_all_suppresses_over_quota_event(quota_manager: QuotaManager) -> None:
    # pre-fill quota
    for _ in range(3):
        quota_manager.record_run("backup")
    events = [_make_event("backup")]
    monitor = QuotaMonitor(_make_monitor(events), quota_manager)
    result = monitor.check_all()
    assert result == []
    assert monitor.suppressed_count == 1
    assert "backup" in monitor.suppressed_jobs


def test_check_all_does_not_suppress_unruled_job(quota_manager: QuotaManager) -> None:
    events = [_make_event("cleanup")]
    monitor = QuotaMonitor(_make_monitor(events), quota_manager)
    result = monitor.check_all()
    assert len(result) == 1
    assert monitor.suppressed_count == 0


def test_suppressed_count_resets_each_call(quota_manager: QuotaManager) -> None:
    for _ in range(3):
        quota_manager.record_run("backup")
    monitor = QuotaMonitor(_make_monitor([_make_event("backup")]), quota_manager)
    monitor.check_all()
    assert monitor.suppressed_count == 1
    monitor._inner.check_all.return_value = []
    monitor.check_all()
    assert monitor.suppressed_count == 0
