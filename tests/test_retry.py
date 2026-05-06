"""Tests for cronwatch.retry module."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from cronwatch.retry import RetryManager, RetryPolicy, RetryState


@pytest.fixture
def policy() -> RetryPolicy:
    return RetryPolicy(max_attempts=3, backoff_seconds=60)


@pytest.fixture
def manager(policy: RetryPolicy) -> RetryManager:
    return RetryManager(policy=policy)


def test_should_retry_true_on_first_attempt(manager: RetryManager) -> None:
    assert manager.should_retry("backup") is True


def test_record_attempt_increments_count(manager: RetryManager) -> None:
    manager.record_attempt("backup")
    state = manager.get_state("backup")
    assert state.attempts == 1


def test_should_retry_false_when_exhausted(manager: RetryManager) -> None:
    for _ in range(3):
        manager.record_attempt("backup")
    # after max attempts, should_retry marks exhausted
    result = manager.should_retry("backup")
    assert result is False
    assert manager.get_state("backup").exhausted is True


def test_should_retry_respects_backoff(manager: RetryManager) -> None:
    manager.record_attempt("backup")  # attempts=1
    # immediately after first attempt, backoff = 60*1 = 60s
    assert manager.should_retry("backup") is False


def test_should_retry_true_after_backoff_elapsed(manager: RetryManager) -> None:
    manager.record_attempt("backup")
    state = manager.get_state("backup")
    # simulate last_attempt being 2 minutes ago
    state.last_attempt = datetime.utcnow() - timedelta(seconds=120)
    assert manager.should_retry("backup") is True


def test_reset_clears_state(manager: RetryManager) -> None:
    manager.record_attempt("backup")
    manager.record_attempt("backup")
    manager.reset("backup")
    state = manager.get_state("backup")
    assert state.attempts == 0
    assert state.last_attempt is None
    assert state.exhausted is False


def test_separate_jobs_have_independent_state(manager: RetryManager) -> None:
    manager.record_attempt("job_a")
    manager.record_attempt("job_a")
    manager.record_attempt("job_b")
    assert manager.get_state("job_a").attempts == 2
    assert manager.get_state("job_b").attempts == 1


def test_exhausted_flag_persists_after_reset_check(manager: RetryManager) -> None:
    for _ in range(3):
        manager.record_attempt("cleanup")
    manager.should_retry("cleanup")  # triggers exhausted
    assert manager.get_state("cleanup").exhausted is True
    manager.reset("cleanup")
    assert manager.get_state("cleanup").exhausted is False
