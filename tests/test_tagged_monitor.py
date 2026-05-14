"""Tests for cronwatch.tagged_monitor."""

from dataclasses import dataclass, field
from typing import List
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.tag_filter import TagFilter
from cronwatch.tagged_monitor import TaggedMonitor


# ── helpers ────────────────────────────────────────────────────────────────────

@dataclass
class FakeJob:
    name: str
    tags: List[str] = field(default_factory=list)


def _make_monitor(jobs):
    monitor = MagicMock()
    monitor.config = MagicMock()
    monitor.config.jobs = jobs
    monitor.check_all = MagicMock()
    return monitor


# ── tests ──────────────────────────────────────────────────────────────────────

def test_check_all_calls_inner_monitor():
    jobs = [FakeJob("job_a", tags=["critical"])]
    monitor = _make_monitor(jobs)
    tm = TaggedMonitor(monitor)
    tm.check_all()
    monitor.check_all.assert_called_once()


def test_check_all_filters_jobs_before_delegating():
    jobs = [
        FakeJob("job_a", tags=["critical"]),
        FakeJob("job_b", tags=["nightly"]),
    ]
    monitor = _make_monitor(jobs)
    tf = TagFilter(include=["critical"])
    tm = TaggedMonitor(monitor, tf)

    seen_jobs = []

    def capture_check():
        seen_jobs.extend(monitor.config.jobs)

    monitor.check_all.side_effect = capture_check
    tm.check_all()

    assert len(seen_jobs) == 1
    assert seen_jobs[0].name == "job_a"


def test_skipped_jobs_populated_after_check_all():
    jobs = [
        FakeJob("job_a", tags=["critical"]),
        FakeJob("job_b", tags=["nightly"]),
    ]
    monitor = _make_monitor(jobs)
    tf = TagFilter(include=["critical"])
    tm = TaggedMonitor(monitor, tf)
    tm.check_all()

    assert "job_b" in tm.skipped_jobs
    assert "job_a" not in tm.skipped_jobs


def test_skipped_count():
    jobs = [
        FakeJob("job_a", tags=["critical"]),
        FakeJob("job_b", tags=["nightly"]),
        FakeJob("job_c", tags=["nightly"]),
    ]
    monitor = _make_monitor(jobs)
    tf = TagFilter(include=["critical"])
    tm = TaggedMonitor(monitor, tf)
    tm.check_all()
    assert tm.skipped_count == 2


def test_original_job_list_restored_after_check():
    jobs = [
        FakeJob("job_a", tags=["critical"]),
        FakeJob("job_b", tags=["nightly"]),
    ]
    monitor = _make_monitor(jobs)
    tf = TagFilter(include=["critical"])
    tm = TaggedMonitor(monitor, tf)
    tm.check_all()

    assert monitor.config.jobs == jobs
