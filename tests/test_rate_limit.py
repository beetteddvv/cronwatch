"""Tests for rate_limit and rate_limited_dispatch modules."""

import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta

from cronwatch.rate_limit import RateLimitRule, RateLimitState, RateLimiter
from cronwatch.rate_limited_dispatch import RateLimitedDispatcher
from cronwatch.alerts import AlertEvent, AlertConfig


@pytest.fixture
def rule():
    return RateLimitRule(max_alerts=3, window_seconds=60)


@pytest.fixture
def limiter(rule):
    return RateLimiter(rule)


@pytest.fixture
def sample_event():
    return AlertEvent(
        job_name="backup",
        reason="missed",
        timestamp=datetime.utcnow(),
        details="No run detected",
    )


def test_is_allowed_true_initially(limiter):
    assert limiter.is_allowed("backup") is True


def test_is_allowed_false_after_limit_reached(limiter):
    for _ in range(3):
        limiter.record("backup")
    assert limiter.is_allowed("backup") is False


def test_current_count_increments(limiter):
    limiter.record("backup")
    limiter.record("backup")
    assert limiter.current_count("backup") == 2


def test_reset_clears_state(limiter):
    limiter.record("backup")
    limiter.reset("backup")
    assert limiter.current_count("backup") == 0


def test_prune_removes_old_timestamps():
    state = RateLimitState()
    old = datetime.utcnow() - timedelta(seconds=120)
    state.timestamps.append(old)
    state.prune(window_seconds=60)
    assert state.count() == 0


def test_rate_limited_dispatch_sends_within_limit(sample_event):
    mock_dispatcher = MagicMock()
    mock_dispatcher.dispatch.return_value = True
    rule = RateLimitRule(max_alerts=5, window_seconds=60)
    rld = RateLimitedDispatcher(mock_dispatcher, rule)

    result = rld.dispatch(sample_event)

    assert result is True
    mock_dispatcher.dispatch.assert_called_once_with(sample_event)


def test_rate_limited_dispatch_suppresses_over_limit(sample_event):
    mock_dispatcher = MagicMock()
    mock_dispatcher.dispatch.return_value = True
    rule = RateLimitRule(max_alerts=2, window_seconds=60)
    rld = RateLimitedDispatcher(mock_dispatcher, rule)

    rld.dispatch(sample_event)
    rld.dispatch(sample_event)
    result = rld.dispatch(sample_event)  # 3rd — should be suppressed

    assert result is False
    assert mock_dispatcher.dispatch.call_count == 2
    assert rld.suppressed_count == 1


def test_rate_limited_dispatch_audits_suppression(sample_event):
    mock_dispatcher = MagicMock()
    mock_dispatcher.dispatch.return_value = True
    mock_audit = MagicMock()
    rule = RateLimitRule(max_alerts=1, window_seconds=60)
    rld = RateLimitedDispatcher(mock_dispatcher, rule, audit_log=mock_audit)

    rld.dispatch(sample_event)
    rld.dispatch(sample_event)  # suppressed

    mock_audit.record.assert_called()
