"""Tests for cronwatch/audit.py"""

import json
import os
import pytest
from cronwatch.audit import AuditEntry, AuditLog


@pytest.fixture
def audit_path(tmp_path):
    return str(tmp_path / "audit.json")


@pytest.fixture
def audit(audit_path):
    return AuditLog(path=audit_path)


def test_audit_entry_to_dict():
    entry = AuditEntry(
        timestamp="2024-01-01T00:00:00",
        event_type="alert_sent",
        job_name="backup",
        detail="overdue by 5 minutes",
        method="email",
    )
    d = entry.to_dict()
    assert d["event_type"] == "alert_sent"
    assert d["job_name"] == "backup"
    assert d["method"] == "email"


def test_audit_entry_roundtrip():
    entry = AuditEntry(
        timestamp="2024-01-01T00:00:00",
        event_type="suppressed",
        job_name="cleanup",
        detail="within silence window",
        method=None,
    )
    restored = AuditEntry.from_dict(entry.to_dict())
    assert restored.job_name == entry.job_name
    assert restored.event_type == entry.event_type
    assert restored.method is None


def test_record_creates_entry(audit):
    entry = audit.record("check_failed", "backup", "missed run")
    assert entry.event_type == "check_failed"
    assert entry.job_name == "backup"
    assert entry.detail == "missed run"


def test_record_increments_count(audit):
    audit.record("alert_sent", "job_a", "overdue", method="email")
    audit.record("alert_sent", "job_b", "overdue", method="webhook")
    assert audit.entry_count == 2


def test_record_persists_to_disk(audit_path, audit):
    audit.record("check_passed", "sync", "on time")
    with open(audit_path) as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["event_type"] == "check_passed"


def test_load_restores_entries(audit_path, audit):
    audit.record("alert_sent", "nightly", "overdue", method="email")
    reloaded = AuditLog(path=audit_path)
    assert reloaded.entry_count == 1
    assert reloaded._entries[0].job_name == "nightly"


def test_get_entries_filter_by_job(audit):
    audit.record("alert_sent", "job_a", "overdue")
    audit.record("alert_sent", "job_b", "overdue")
    results = audit.get_entries(job_name="job_a")
    assert len(results) == 1
    assert results[0].job_name == "job_a"


def test_get_entries_filter_by_event_type(audit):
    audit.record("alert_sent", "job_a", "overdue")
    audit.record("suppressed", "job_a", "silence window")
    results = audit.get_entries(event_type="suppressed")
    assert len(results) == 1
    assert results[0].event_type == "suppressed"


def test_clear_removes_all_entries(audit):
    audit.record("alert_sent", "job_a", "overdue")
    audit.clear()
    assert audit.entry_count == 0


def test_load_handles_corrupt_file(tmp_path):
    bad_path = str(tmp_path / "bad_audit.json")
    with open(bad_path, "w") as f:
        f.write("not valid json{{")
    log = AuditLog(path=bad_path)
    assert log.entry_count == 0
