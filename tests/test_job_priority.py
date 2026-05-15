"""Tests for cronwatch.job_priority."""
import pytest

from cronwatch.job_priority import Priority, PriorityManager, load_priority_rules


# ---------------------------------------------------------------------------
# Priority enum
# ---------------------------------------------------------------------------

def test_priority_ordering():
    assert Priority.LOW < Priority.NORMAL < Priority.HIGH < Priority.CRITICAL


def test_priority_from_str_valid():
    assert Priority.from_str("high") == Priority.HIGH
    assert Priority.from_str("CRITICAL") == Priority.CRITICAL


def test_priority_from_str_invalid():
    with pytest.raises(ValueError, match="Unknown priority"):
        Priority.from_str("urgent")


# ---------------------------------------------------------------------------
# PriorityManager
# ---------------------------------------------------------------------------

@pytest.fixture
def manager():
    m = PriorityManager()
    m.set_priority("backup", Priority.HIGH)
    m.set_priority("cleanup", Priority.LOW)
    return m


def test_get_priority_returns_set_value(manager):
    assert manager.get_priority("backup") == Priority.HIGH


def test_get_priority_defaults_to_normal(manager):
    assert manager.get_priority("unknown_job") == Priority.NORMAL


def test_jobs_at_or_above_filters_correctly(manager):
    result = manager.jobs_at_or_above(Priority.HIGH)
    assert "backup" in result
    assert "cleanup" not in result


def test_all_rules_returns_copy(manager):
    rules = manager.all_rules()
    rules["extra"] = Priority.CRITICAL
    assert "extra" not in manager.all_rules()


# ---------------------------------------------------------------------------
# load_priority_rules
# ---------------------------------------------------------------------------

def test_load_priority_rules_parses_entries():
    raw = [
        {"job": "nightly", "priority": "critical"},
        {"job": "weekly", "priority": "low"},
    ]
    mgr = load_priority_rules(raw)
    assert mgr.get_priority("nightly") == Priority.CRITICAL
    assert mgr.get_priority("weekly") == Priority.LOW


def test_load_priority_rules_defaults_missing_priority():
    raw = [{"job": "daily"}]
    mgr = load_priority_rules(raw)
    assert mgr.get_priority("daily") == Priority.NORMAL
