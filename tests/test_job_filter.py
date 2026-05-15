"""Tests for JobFilter and FilteredMonitor."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List
from unittest.mock import MagicMock

import pytest

from cronwatch.job_filter import JobFilter, JobFilterCriteria
from cronwatch.filtered_monitor import FilteredMonitor


@dataclass
class FakeJob:
    name: str
    schedule: str
    tags: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def jobs():
    return [
        FakeJob("backup-daily", "0 2 * * *", tags=["ops", "backup"]),
        FakeJob("report-weekly", "0 9 * * 1", tags=["ops", "report"]),
        FakeJob("cleanup-hourly", "0 * * * *", tags=["dev"]),
        FakeJob("ping-check", "*/5 * * * *", tags=[]),
    ]


# ---------------------------------------------------------------------------
# JobFilter.matches — name_pattern
# ---------------------------------------------------------------------------

def test_matches_name_wildcard_hit(jobs):
    f = JobFilter(JobFilterCriteria(name_pattern="backup-*"))
    assert f.matches(jobs[0]) is True


def test_matches_name_wildcard_miss(jobs):
    f = JobFilter(JobFilterCriteria(name_pattern="backup-*"))
    assert f.matches(jobs[1]) is False


# ---------------------------------------------------------------------------
# JobFilter.matches — schedule_contains
# ---------------------------------------------------------------------------

def test_matches_schedule_substring_hit(jobs):
    f = JobFilter(JobFilterCriteria(schedule_contains="* * *"))
    assert f.matches(jobs[0]) is True


def test_matches_schedule_substring_miss(jobs):
    f = JobFilter(JobFilterCriteria(schedule_contains="*/5"))
    assert f.matches(jobs[0]) is False


# ---------------------------------------------------------------------------
# JobFilter.matches — tags_any
# ---------------------------------------------------------------------------

def test_matches_tags_any_hit(jobs):
    f = JobFilter(JobFilterCriteria(tags_any=["backup"]))
    assert f.matches(jobs[0]) is True


def test_matches_tags_any_miss(jobs):
    f = JobFilter(JobFilterCriteria(tags_any=["backup"]))
    assert f.matches(jobs[2]) is False


# ---------------------------------------------------------------------------
# JobFilter.matches — tags_all
# ---------------------------------------------------------------------------

def test_matches_tags_all_hit(jobs):
    f = JobFilter(JobFilterCriteria(tags_all=["ops", "backup"]))
    assert f.matches(jobs[0]) is True


def test_matches_tags_all_miss_partial(jobs):
    f = JobFilter(JobFilterCriteria(tags_all=["ops", "backup"]))
    assert f.matches(jobs[1]) is False  # has ops but not backup


# ---------------------------------------------------------------------------
# JobFilter.apply / excluded
# ---------------------------------------------------------------------------

def test_apply_returns_subset(jobs):
    f = JobFilter(JobFilterCriteria(tags_any=["ops"]))
    result = f.apply(jobs)
    assert len(result) == 2
    assert all("ops" in j.tags for j in result)


def test_excluded_is_complement(jobs):
    f = JobFilter(JobFilterCriteria(tags_any=["ops"]))
    assert len(f.excluded(jobs)) == 2


# ---------------------------------------------------------------------------
# FilteredMonitor
# ---------------------------------------------------------------------------

def _make_filtered_monitor(jobs, criteria):
    inner = MagicMock()
    inner.config.jobs = jobs
    inner.check_all = MagicMock()
    return FilteredMonitor(inner, criteria), inner


def test_filtered_monitor_delegates_to_inner(jobs):
    fm, inner = _make_filtered_monitor(jobs, JobFilterCriteria(tags_any=["ops"]))
    fm.check_all()
    inner.check_all.assert_called_once()


def test_filtered_monitor_skipped_count(jobs):
    fm, _ = _make_filtered_monitor(jobs, JobFilterCriteria(tags_any=["ops"]))
    fm.check_all()
    assert fm.skipped_count == 2


def test_filtered_monitor_restores_original_jobs(jobs):
    fm, inner = _make_filtered_monitor(jobs, JobFilterCriteria(tags_any=["ops"]))
    fm.check_all()
    assert inner.config.jobs is jobs
