"""Tests for SnapshotStore and Snapshot dataclass."""

import json
import os
import pytest
from datetime import datetime, timezone

from cronwatch.snapshot import Snapshot, SnapshotStore


def _snap(**kwargs) -> Snapshot:
    defaults = dict(
        timestamp=datetime.now(timezone.utc).isoformat(),
        total_jobs=5,
        healthy=4,
        failing=1,
        silenced=0,
        overdue=1,
    )
    defaults.update(kwargs)
    return Snapshot(**defaults)


@pytest.fixture
def store(tmp_path):
    return SnapshotStore(str(tmp_path / "snaps.json"))


def test_snapshot_to_dict_has_expected_keys():
    s = _snap()
    d = s.to_dict()
    assert set(d.keys()) == {"timestamp", "total_jobs", "healthy", "failing", "silenced", "overdue", "extra"}


def test_snapshot_roundtrip():
    s = _snap(extra={"source": "test"})
    d = s.to_dict()
    s2 = Snapshot.from_dict(d)
    assert s2.healthy == s.healthy
    assert s2.extra == {"source": "test"}


def test_store_record_persists(store, tmp_path):
    store.record(_snap(healthy=3))
    store2 = SnapshotStore(str(tmp_path / "snaps.json"))
    assert len(store2.all()) == 1
    assert store2.latest().healthy == 3


def test_store_latest_none_when_empty(store):
    assert store.latest() is None


def test_store_max_snapshots_trimmed(tmp_path):
    store = SnapshotStore(str(tmp_path / "snaps.json"), max_snapshots=3)
    for i in range(5):
        store.record(_snap(healthy=i))
    assert len(store.all()) == 3
    assert store.latest().healthy == 4


def test_store_since_filters_correctly(store):
    from datetime import timedelta
    old_ts = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    new_ts = datetime.now(timezone.utc).isoformat()
    store.record(_snap(timestamp=old_ts, healthy=1))
    store.record(_snap(timestamp=new_ts, healthy=2))
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    recent = store.since(cutoff)
    assert len(recent) == 1
    assert recent[0].healthy == 2
