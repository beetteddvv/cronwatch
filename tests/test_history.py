"""Tests for cronwatch.history module."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, mock_open
from cronwatch.history import RunRecord, HistoryStore


@pytest.fixture
def store(tmp_path):
    return HistoryStore(path=str(tmp_path / "history.json"))


@pytest.fixture
def sample_record():
    return RunRecord(
        job_name="backup",
        started_at=datetime(2024, 1, 15, 10, 0, 0),
        finished_at=datetime(2024, 1, 15, 10, 0, 30),
        exit_code=0,
        success=True,
    )


@pytest.fixture
def failed_record():
    return RunRecord(
        job_name="backup",
        started_at=datetime(2024, 1, 15, 11, 0, 0),
        finished_at=datetime(2024, 1, 15, 11, 0, 5),
        exit_code=1,
        success=False,
        notes="non-zero exit",
    )


def test_run_record_to_dict(sample_record):
    d = sample_record.to_dict()
    assert d["job_name"] == "backup"
    assert d["success"] is True
    assert d["exit_code"] == 0
    assert "started_at" in d


def test_run_record_roundtrip(sample_record):
    restored = RunRecord.from_dict(sample_record.to_dict())
    assert restored.job_name == sample_record.job_name
    assert restored.started_at == sample_record.started_at
    assert restored.success == sample_record.success


def test_append_stores_record(store, sample_record):
    store.append(sample_record)
    results = store.get_for_job("backup")
    assert len(results) == 1
    assert results[0].job_name == "backup"


def test_get_for_job_returns_only_matching(store, sample_record):
    other = RunRecord(job_name="cleanup", started_at=datetime.now(), success=True)
    store.append(sample_record)
    store.append(other)
    results = store.get_for_job("backup")
    assert all(r.job_name == "backup" for r in results)


def test_get_recent_failures_filters_successes(store, sample_record, failed_record):
    store.append(sample_record)
    store.append(failed_record)
    failures = store.get_recent_failures("backup")
    assert len(failures) == 1
    assert failures[0].success is False


def test_failure_count(store, sample_record, failed_record):
    store.append(sample_record)
    store.append(failed_record)
    store.append(failed_record)
    assert store.failure_count("backup") == 2


def test_max_records_trimmed(tmp_path):
    store = HistoryStore(path=str(tmp_path / "h.json"), max_records=3)
    for i in range(5):
        store.append(RunRecord(job_name="job", started_at=datetime.now(), success=True))
    assert len(store._records) == 3


def test_get_for_job_respects_limit(store):
    for i in range(8):
        store.append(RunRecord(job_name="job", started_at=datetime.now(), success=True))
    results = store.get_for_job("job", limit=5)
    assert len(results) == 5
