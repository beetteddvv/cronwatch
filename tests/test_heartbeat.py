"""Tests for HeartbeatTracker."""

import time
from unittest.mock import MagicMock

import pytest

from cronwatch.heartbeat import HeartbeatTracker, HeartbeatRecord


@pytest.fixture
def mock_store():
    store = MagicMock()
    store.get_last_run.return_value = None
    return store


@pytest.fixture
def tracker(mock_store):
    return HeartbeatTracker(store=mock_store, tolerance=1.2)


def test_ping_creates_record(tracker):
    tracker.ping("backup", expected_interval=3600)
    record = tracker.get_record("backup")
    assert record is not None
    assert record.job_name == "backup"
    assert record.missed_count == 0


def test_ping_calls_store_update(tracker, mock_store):
    tracker.ping("backup", expected_interval=3600)
    mock_store.update_last_run.assert_called_once()
    args = mock_store.update_last_run.call_args[0]
    assert args[0] == "backup"


def test_is_silent_false_after_fresh_ping(tracker):
    tracker.ping("backup", expected_interval=3600)
    assert tracker.is_silent("backup") is False


def test_is_silent_true_when_overdue(tracker):
    tracker.ping("backup", expected_interval=1)
    record = tracker.get_record("backup")
    # Backdate the ping so the deadline has passed
    record.last_ping = time.time() - 10
    assert tracker.is_silent("backup") is True


def test_is_silent_false_for_unknown_job_with_no_store_data(tracker, mock_store):
    mock_store.get_last_run.return_value = None
    assert tracker.is_silent("nonexistent") is False


def test_increment_missed_returns_new_count(tracker):
    tracker.ping("backup", expected_interval=3600)
    count = tracker.increment_missed("backup")
    assert count == 1
    count = tracker.increment_missed("backup")
    assert count == 2


def test_increment_missed_unknown_job_returns_zero(tracker):
    assert tracker.increment_missed("ghost") == 0


def test_reset_removes_record(tracker):
    tracker.ping("backup", expected_interval=3600)
    tracker.reset("backup")
    assert tracker.get_record("backup") is None


def test_reset_nonexistent_job_does_not_raise(tracker):
    tracker.reset("ghost")  # should not raise
