"""Tests for cronwatch/job_sla.py"""

from datetime import datetime, timedelta

import pytest

from cronwatch.job_sla import SLAManager, SLARule, SLAViolation


@pytest.fixture
def rule():
    return SLARule(job_name="backup", max_duration_seconds=60, warn_at_percent=0.8)


@pytest.fixture
def manager(rule):
    m = SLAManager()
    m.add_rule(rule)
    return m


def _now():
    return datetime(2024, 1, 1, 12, 0, 0)


def test_check_returns_none_before_start(manager):
    result = manager.check("backup", at=_now())
    assert result is None


def test_check_returns_none_within_warn_window(manager):
    start = _now()
    manager.start_job("backup", at=start)
    just_inside = start + timedelta(seconds=40)  # 40 < 48 (80% of 60)
    assert manager.check("backup", at=just_inside) is None


def test_check_returns_warning_at_warn_threshold(manager):
    start = _now()
    manager.start_job("backup", at=start)
    at_warn = start + timedelta(seconds=49)  # 49 >= 48
    violation = manager.check("backup", at=at_warn)
    assert violation is not None
    assert violation.is_warning is True
    assert violation.job_name == "backup"


def test_check_returns_breach_at_limit(manager):
    start = _now()
    manager.start_job("backup", at=start)
    at_breach = start + timedelta(seconds=61)
    violation = manager.check("backup", at=at_breach)
    assert violation is not None
    assert violation.is_warning is False


def test_warning_only_fires_once(manager):
    start = _now()
    manager.start_job("backup", at=start)
    at_warn = start + timedelta(seconds=49)
    first = manager.check("backup", at=at_warn)
    second = manager.check("backup", at=at_warn + timedelta(seconds=1))
    assert first is not None and first.is_warning
    # second check still below breach — should be None (already warned)
    assert second is None


def test_complete_job_removes_state(manager):
    start = _now()
    manager.start_job("backup", at=start)
    manager.complete_job("backup")
    assert manager.check("backup", at=start + timedelta(seconds=100)) is None
    assert "backup" not in manager.active_jobs()


def test_violation_str_breach():
    v = SLAViolation(
        job_name="etl",
        started_at=_now(),
        elapsed_seconds=120.5,
        limit_seconds=60,
        is_warning=False,
    )
    assert "BREACH" in str(v)
    assert "etl" in str(v)


def test_violation_str_warning():
    v = SLAViolation(
        job_name="etl",
        started_at=_now(),
        elapsed_seconds=50.0,
        limit_seconds=60,
        is_warning=True,
    )
    assert "WARNING" in str(v)


def test_no_rule_returns_none(manager):
    manager.start_job("unknown_job", at=_now())
    result = manager.check("unknown_job", at=_now() + timedelta(seconds=999))
    assert result is None
