"""Tests for alert throttling logic."""

from datetime import datetime, timedelta
import pytest

from cronwatch.throttle import AlertThrottle, ThrottleRule


@pytest.fixture
def rule():
    return ThrottleRule(min_interval_seconds=60, max_alerts_per_hour=3)


@pytest.fixture
def throttle(rule):
    return AlertThrottle(rule=rule)


def test_should_send_true_on_first_alert(throttle):
    assert throttle.should_send("backup") is True


def test_should_send_false_before_min_interval(throttle):
    now = datetime(2024, 1, 1, 12, 0, 0)
    throttle.record_send("backup", now=now)
    soon = now + timedelta(seconds=30)
    assert throttle.should_send("backup", now=soon) is False


def test_should_send_true_after_min_interval(throttle):
    now = datetime(2024, 1, 1, 12, 0, 0)
    throttle.record_send("backup", now=now)
    later = now + timedelta(seconds=90)
    assert throttle.should_send("backup", now=later) is True


def test_should_send_false_when_hourly_cap_reached(throttle):
    base = datetime(2024, 1, 1, 12, 0, 0)
    for i in range(3):
        t = base + timedelta(seconds=i * 90)
        assert throttle.should_send("job", now=t) is True
        throttle.record_send("job", now=t)
    # 4th attempt within same hour window
    t_next = base + timedelta(seconds=3 * 90)
    assert throttle.should_send("job", now=t_next) is False


def test_hourly_cap_resets_after_one_hour(throttle):
    base = datetime(2024, 1, 1, 12, 0, 0)
    for i in range(3):
        t = base + timedelta(seconds=i * 90)
        throttle.record_send("job", now=t)
    new_hour = base + timedelta(hours=1, seconds=10)
    assert throttle.should_send("job", now=new_hour) is True


def test_reset_clears_state(throttle):
    now = datetime(2024, 1, 1, 12, 0, 0)
    throttle.record_send("job", now=now)
    throttle.reset("job")
    soon = now + timedelta(seconds=10)
    assert throttle.should_send("job", now=soon) is True


def test_different_jobs_are_independent(throttle):
    now = datetime(2024, 1, 1, 12, 0, 0)
    throttle.record_send("job_a", now=now)
    # job_b should not be affected
    assert throttle.should_send("job_b", now=now) is True


def test_default_rule_used_when_none_provided():
    t = AlertThrottle()
    assert t.rule.min_interval_seconds == 300
    assert t.rule.max_alerts_per_hour == 10
