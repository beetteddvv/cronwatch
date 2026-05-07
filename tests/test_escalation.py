"""Tests for cronwatch.escalation."""

import pytest
from cronwatch.escalation import EscalationPolicy, EscalationManager


@pytest.fixture
def policy():
    return EscalationPolicy(threshold=3, escalated_channel="email", reset_on_success=True)


@pytest.fixture
def manager(policy):
    return EscalationManager(policy)


def test_initial_failure_count_is_zero(manager):
    assert manager.failure_count("job_a") == 0


def test_record_failure_increments_count(manager):
    manager.record_failure("job_a")
    manager.record_failure("job_a")
    assert manager.failure_count("job_a") == 2


def test_not_escalated_before_threshold(manager):
    manager.record_failure("job_a")
    manager.record_failure("job_a")
    assert not manager.is_escalated("job_a")


def test_escalated_at_threshold(manager):
    for _ in range(3):
        manager.record_failure("job_a")
    assert manager.is_escalated("job_a")


def test_record_failure_returns_true_on_escalation(manager):
    manager.record_failure("job_a")
    manager.record_failure("job_a")
    result = manager.record_failure("job_a")
    assert result is True


def test_record_failure_returns_false_before_escalation(manager):
    result = manager.record_failure("job_a")
    assert result is False


def test_record_failure_returns_false_after_already_escalated(manager):
    for _ in range(3):
        manager.record_failure("job_a")
    result = manager.record_failure("job_a")  # 4th failure
    assert result is False


def test_record_success_resets_state(manager):
    for _ in range(3):
        manager.record_failure("job_a")
    manager.record_success("job_a")
    assert not manager.is_escalated("job_a")
    assert manager.failure_count("job_a") == 0


def test_channel_for_returns_default_before_escalation(manager):
    manager.record_failure("job_a")
    assert manager.channel_for("job_a", "log") == "log"


def test_channel_for_returns_escalated_channel_after_threshold(manager):
    for _ in range(3):
        manager.record_failure("job_a")
    assert manager.channel_for("job_a", "log") == "email"


def test_independent_state_per_job(manager):
    for _ in range(3):
        manager.record_failure("job_a")
    assert not manager.is_escalated("job_b")
