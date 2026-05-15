"""Tests for cronwatch.job_quota."""

from datetime import datetime, timedelta

import pytest

from cronwatch.job_quota import QuotaManager, QuotaRule


@pytest.fixture
def rule() -> QuotaRule:
    return QuotaRule(max_runs=3, window_seconds=60)


@pytest.fixture
def manager(rule: QuotaRule) -> QuotaManager:
    m = QuotaManager()
    m.set_rule("backup", rule)
    return m


NOW = datetime(2024, 1, 1, 12, 0, 0)


def test_is_over_quota_false_initially(manager: QuotaManager) -> None:
    assert manager.is_over_quota("backup", now=NOW) is False


def test_run_count_zero_initially(manager: QuotaManager) -> None:
    assert manager.run_count("backup", now=NOW) == 0


def test_record_run_increments_count(manager: QuotaManager) -> None:
    manager.record_run("backup", now=NOW)
    assert manager.run_count("backup", now=NOW) == 1


def test_is_over_quota_true_after_exceeding_limit(manager: QuotaManager) -> None:
    for i in range(4):
        manager.record_run("backup", now=NOW + timedelta(seconds=i))
    assert manager.is_over_quota("backup", now=NOW + timedelta(seconds=4)) is True


def test_is_over_quota_false_after_window_expires(manager: QuotaManager) -> None:
    for i in range(4):
        manager.record_run("backup", now=NOW + timedelta(seconds=i))
    future = NOW + timedelta(seconds=120)
    assert manager.is_over_quota("backup", now=future) is False


def test_no_rule_never_over_quota(manager: QuotaManager) -> None:
    for _ in range(100):
        manager.record_run("other_job", now=NOW)
    assert manager.is_over_quota("other_job", now=NOW) is False


def test_prune_removes_old_entries(manager: QuotaManager) -> None:
    manager.record_run("backup", now=NOW)
    manager.record_run("backup", now=NOW + timedelta(seconds=10))
    future = NOW + timedelta(seconds=80)
    count = manager.run_count("backup", now=future)
    assert count == 1
