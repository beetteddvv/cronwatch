"""Tests for CooldownMonitor."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from cronwatch.alerts import AlertEvent
from cronwatch.cooldown_monitor import CooldownMonitor
from cronwatch.job_cooldown import CooldownManager, CooldownRule


def _make_event(job_name: str) -> AlertEvent:
    return AlertEvent(
        job_name=job_name,
        reason="missed",
        timestamp=datetime(2024, 3, 15, 10, 0, 0),
    )


@pytest.fixture
def cooldown_manager() -> CooldownManager:
    m = CooldownManager()
    m.add_rule(CooldownRule(job_name="backup", cooldown_seconds=300))
    return m


def _make_monitor(events, cooldown_manager):
    inner = MagicMock()
    inner.check_all.return_value = events
    return CooldownMonitor(inner=inner, cooldown_manager=cooldown_manager)


def test_check_all_passes_events_not_in_cooldown(cooldown_manager):
    events = [_make_event("backup"), _make_event("deploy")]
    monitor = _make_monitor(events, cooldown_manager)
    result = monitor.check_all()
    assert len(result) == 2


def test_check_all_suppresses_cooling_down_job(cooldown_manager):
    now = datetime(2024, 3, 15, 10, 0, 0)
    cooldown_manager.mark_recovered("backup", now=now)
    events = [_make_event("backup")]
    monitor = _make_monitor(events, cooldown_manager)
    result = monitor.check_all()
    assert result == []
    assert monitor.suppressed_count == 1
    assert "backup" in monitor.suppressed_jobs


def test_check_all_allows_non_cooling_job(cooldown_manager):
    now = datetime(2024, 3, 15, 10, 0, 0)
    cooldown_manager.mark_recovered("backup", now=now)
    events = [_make_event("backup"), _make_event("sync")]
    monitor = _make_monitor(events, cooldown_manager)
    result = monitor.check_all()
    assert len(result) == 1
    assert result[0].job_name == "sync"


def test_suppressed_count_resets_each_check(cooldown_manager):
    now = datetime(2024, 3, 15, 10, 0, 0)
    cooldown_manager.mark_recovered("backup", now=now)
    events = [_make_event("backup")]
    monitor = _make_monitor(events, cooldown_manager)
    monitor.check_all()
    assert monitor.suppressed_count == 1
    # second call with no events — suppressed should reset
    monitor._inner.check_all.return_value = []
    monitor.check_all()
    assert monitor.suppressed_count == 0


def test_mark_recovered_triggers_cooldown(cooldown_manager):
    now = datetime(2024, 3, 15, 10, 0, 0)
    events = [_make_event("backup")]
    monitor = _make_monitor(events, cooldown_manager)
    monitor.mark_recovered("backup")
    # immediately after recovery, job should be in cooldown
    assert cooldown_manager.is_cooling_down("backup") is True
