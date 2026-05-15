"""Tests for job_lifecycle.py."""

from datetime import datetime

import pytest

from cronwatch.job_lifecycle import (
    JobLifecycleTracker,
    LifecycleEvent,
    LifecycleState,
)


def test_lifecycle_state_from_str_valid():
    assert LifecycleState.from_str("running") == LifecycleState.RUNNING


def test_lifecycle_state_from_str_invalid():
    assert LifecycleState.from_str("bogus") == LifecycleState.UNKNOWN


def test_lifecycle_event_to_dict_has_expected_keys():
    event = LifecycleEvent(job_name="backup", state=LifecycleState.COMPLETED)
    d = event.to_dict()
    assert set(d.keys()) == {"job_name", "state", "timestamp", "message"}


def test_lifecycle_event_roundtrip():
    original = LifecycleEvent(
        job_name="cleanup",
        state=LifecycleState.FAILED,
        timestamp=datetime(2024, 1, 15, 10, 30),
        message="exit code 1",
    )
    restored = LifecycleEvent.from_dict(original.to_dict())
    assert restored.job_name == original.job_name
    assert restored.state == original.state
    assert restored.message == original.message


def test_tracker_initial_state_is_unknown():
    tracker = JobLifecycleTracker()
    assert tracker.current_state("nonexistent") == LifecycleState.UNKNOWN


def test_tracker_transition_updates_state():
    tracker = JobLifecycleTracker()
    tracker.transition("job1", LifecycleState.RUNNING)
    assert tracker.current_state("job1") == LifecycleState.RUNNING


def test_tracker_transition_returns_event():
    tracker = JobLifecycleTracker()
    event = tracker.transition("job1", LifecycleState.COMPLETED, message="ok")
    assert isinstance(event, LifecycleEvent)
    assert event.message == "ok"


def test_tracker_last_event_none_for_unknown_job():
    tracker = JobLifecycleTracker()
    assert tracker.last_event("ghost") is None


def test_tracker_jobs_in_state():
    tracker = JobLifecycleTracker()
    tracker.transition("a", LifecycleState.FAILED)
    tracker.transition("b", LifecycleState.COMPLETED)
    tracker.transition("c", LifecycleState.FAILED)
    failed = tracker.jobs_in_state(LifecycleState.FAILED)
    assert set(failed) == {"a", "c"}


def test_tracker_reset_removes_job():
    tracker = JobLifecycleTracker()
    tracker.transition("job1", LifecycleState.RUNNING)
    tracker.reset("job1")
    assert tracker.current_state("job1") == LifecycleState.UNKNOWN


def test_tracker_all_states_returns_dict():
    tracker = JobLifecycleTracker()
    tracker.transition("x", LifecycleState.PENDING)
    states = tracker.all_states()
    assert states["x"] == LifecycleState.PENDING
