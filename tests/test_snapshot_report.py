"""Tests for SnapshotReporter trend analysis."""

import pytest
from datetime import datetime, timedelta, timezone

from cronwatch.snapshot import Snapshot, SnapshotStore
from cronwatch.snapshot_report import SnapshotReporter, SnapshotTrend


def _snap(healthy=4, failing=1, overdue=1, hours_ago=0) -> Snapshot:
    ts = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
    return Snapshot(
        timestamp=ts,
        total_jobs=5,
        healthy=healthy,
        failing=failing,
        silenced=0,
        overdue=overdue,
    )


@pytest.fixture
def store(tmp_path):
    s = SnapshotStore(str(tmp_path / "snaps.json"))
    s.record(_snap(healthy=4, failing=1, overdue=1, hours_ago=0))
    s.record(_snap(healthy=3, failing=2, overdue=2, hours_ago=1))
    s.record(_snap(healthy=5, failing=0, overdue=0, hours_ago=2))
    return s


@pytest.fixture
def reporter(store):
    return SnapshotReporter(store)


def test_trend_returns_trend_type(reporter):
    result = reporter.trend(hours=24)
    assert isinstance(result, SnapshotTrend)


def test_trend_sample_count(reporter):
    result = reporter.trend(hours=24)
    assert result.sample_count == 3


def test_trend_avg_healthy(reporter):
    result = reporter.trend(hours=24)
    assert abs(result.avg_healthy - 4.0) < 0.01


def test_trend_peak_overdue(reporter):
    result = reporter.trend(hours=24)
    assert result.peak_overdue == 2


def test_trend_peak_failing(reporter):
    result = reporter.trend(hours=24)
    assert result.peak_failing == 2


def test_trend_none_when_no_samples(tmp_path):
    empty_store = SnapshotStore(str(tmp_path / "empty.json"))
    reporter = SnapshotReporter(empty_store)
    assert reporter.trend(hours=1) is None


def test_trend_summary_is_string(reporter):
    result = reporter.trend(hours=24)
    assert isinstance(result.summary(), str)
    assert "Last 24h" in result.summary()
