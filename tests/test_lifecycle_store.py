"""Tests for lifecycle_store.py."""

import tempfile
from pathlib import Path

import pytest

from cronwatch.job_lifecycle import LifecycleEvent, LifecycleState
from cronwatch.lifecycle_store import LifecycleStore


@pytest.fixture
def store(tmp_path):
    return LifecycleStore(str(tmp_path / "lifecycle.jsonl"))


def _event(name: str, state: LifecycleState, message: str = "") -> LifecycleEvent:
    return LifecycleEvent(job_name=name, state=state, message=message)


def test_store_creates_file(tmp_path):
    path = str(tmp_path / "sub" / "lc.jsonl")
    LifecycleStore(path)
    assert Path(path).exists()


def test_record_and_read_all(store):
    store.record(_event("job1", LifecycleState.COMPLETED))
    store.record(_event("job2", LifecycleState.FAILED))
    events = store.read_all()
    assert len(events) == 2


def test_read_all_returns_correct_types(store):
    store.record(_event("job1", LifecycleState.RUNNING))
    events = store.read_all()
    assert isinstance(events[0], LifecycleEvent)


def test_events_for_job_filters_correctly(store):
    store.record(_event("alpha", LifecycleState.COMPLETED))
    store.record(_event("beta", LifecycleState.FAILED))
    store.record(_event("alpha", LifecycleState.FAILED))
    alpha_events = store.events_for_job("alpha")
    assert len(alpha_events) == 2
    assert all(e.job_name == "alpha" for e in alpha_events)


def test_last_event_for_job_returns_most_recent(store):
    store.record(_event("job1", LifecycleState.RUNNING))
    store.record(_event("job1", LifecycleState.COMPLETED))
    last = store.last_event_for_job("job1")
    assert last.state == LifecycleState.COMPLETED


def test_last_event_for_missing_job_returns_none(store):
    assert store.last_event_for_job("ghost") is None


def test_events_in_state(store):
    store.record(_event("a", LifecycleState.FAILED))
    store.record(_event("b", LifecycleState.COMPLETED))
    store.record(_event("c", LifecycleState.FAILED))
    failed = store.events_in_state(LifecycleState.FAILED)
    assert len(failed) == 2


def test_clear_removes_all_events(store):
    store.record(_event("job1", LifecycleState.COMPLETED))
    store.clear()
    assert store.read_all() == []
