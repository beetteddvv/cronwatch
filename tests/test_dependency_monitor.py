"""Tests for DependencyAwareMonitor."""

from __future__ import annotations

from typing import List
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.dependency import DependencyChecker, DependencyGraph
from cronwatch.dependency_monitor import DependencyAwareMonitor


def _make_job(name: str) -> MagicMock:
    job = MagicMock()
    job.name = name
    return job


@pytest.fixture
def graph() -> DependencyGraph:
    g = DependencyGraph()
    g.register("fetch")
    g.register("transform", depends_on=["fetch"])
    return g


@pytest.fixture
def monitor_fixture(graph):
    monitor = MagicMock()
    monitor.config.jobs = [_make_job("fetch"), _make_job("transform")]
    checker = DependencyChecker(graph)
    dep_monitor = DependencyAwareMonitor(monitor, checker)
    return dep_monitor, monitor


def test_check_all_runs_job_with_no_deps(monitor_fixture):
    dep_monitor, inner = monitor_fixture
    dep_monitor.check_all()
    # fetch has no deps — should be checked
    calls = [call.args[0].name for call in inner._check_job.call_args_list]
    assert "fetch" in calls


def test_check_all_skips_job_with_unmet_deps(monitor_fixture):
    dep_monitor, inner = monitor_fixture
    dep_monitor.check_all()
    calls = [call.args[0].name for call in inner._check_job.call_args_list]
    assert "transform" not in calls


def test_check_all_runs_job_when_deps_met(monitor_fixture):
    dep_monitor, inner = monitor_fixture
    dep_monitor.mark_completed("fetch")
    dep_monitor.check_all()
    calls = [call.args[0].name for call in inner._check_job.call_args_list]
    assert "transform" in calls


def test_violations_recorded_for_skipped_jobs(monitor_fixture):
    dep_monitor, _ = monitor_fixture
    dep_monitor.check_all()
    assert dep_monitor.violation_count == 1
    assert dep_monitor.violations[0].job_name == "transform"


def test_no_violations_when_all_deps_met(monitor_fixture):
    dep_monitor, _ = monitor_fixture
    dep_monitor.mark_completed("fetch")
    dep_monitor.check_all()
    assert dep_monitor.violation_count == 0


def test_mark_completed_accumulates(monitor_fixture):
    dep_monitor, _ = monitor_fixture
    dep_monitor.mark_completed("fetch")
    dep_monitor.mark_completed("transform")
    assert dep_monitor._completed == {"fetch", "transform"}
