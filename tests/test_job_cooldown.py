"""Tests for CooldownRule, CooldownState, and CooldownManager."""

from datetime import datetime, timedelta

import pytest

from cronwatch.job_cooldown import CooldownManager, CooldownRule, CooldownState


@pytest.fixture
def rule() -> CooldownRule:
    return CooldownRule(job_name="backup", cooldown_seconds=300)


@pytest.fixture
def manager() -> CooldownManager:
    m = CooldownManager()
    m.add_rule(CooldownRule(job_name="backup", cooldown_seconds=300))
    return m


def test_cooldown_state_not_cooling_before_recovery(rule):
    state = CooldownState(job_name="backup")
    assert state.is_cooling_down(rule) is False


def test_cooldown_state_cooling_immediately_after_recovery(rule):
    state = CooldownState(job_name="backup")
    now = datetime(2024, 1, 1, 12, 0, 0)
    state.mark_recovered(now=now)
    assert state.is_cooling_down(rule, now=now) is True


def test_cooldown_state_not_cooling_after_window_expires(rule):
    state = CooldownState(job_name="backup")
    recovered_at = datetime(2024, 1, 1, 12, 0, 0)
    state.mark_recovered(now=recovered_at)
    later = recovered_at + timedelta(seconds=301)
    assert state.is_cooling_down(rule, now=later) is False


def test_cooldown_state_clear_resets(rule):
    state = CooldownState(job_name="backup")
    state.mark_recovered()
    state.clear()
    assert state.recovered_at is None
    assert state.is_cooling_down(rule) is False


def test_manager_not_cooling_without_rule():
    m = CooldownManager()
    m.mark_recovered("unknown_job")
    assert m.is_cooling_down("unknown_job") is False


def test_manager_cooling_after_mark_recovered(manager):
    now = datetime(2024, 6, 1, 8, 0, 0)
    manager.mark_recovered("backup", now=now)
    assert manager.is_cooling_down("backup", now=now) is True


def test_manager_not_cooling_after_window(manager):
    now = datetime(2024, 6, 1, 8, 0, 0)
    manager.mark_recovered("backup", now=now)
    later = now + timedelta(seconds=400)
    assert manager.is_cooling_down("backup", now=later) is False


def test_manager_clear_stops_cooldown(manager):
    now = datetime(2024, 6, 1, 8, 0, 0)
    manager.mark_recovered("backup", now=now)
    manager.clear("backup")
    assert manager.is_cooling_down("backup", now=now) is False


def test_manager_rule_for_returns_rule(manager):
    rule = manager.rule_for("backup")
    assert rule is not None
    assert rule.cooldown_seconds == 300


def test_manager_rule_for_missing_returns_none(manager):
    assert manager.rule_for("nonexistent") is None
