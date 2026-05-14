"""Tests for DependencyGraph, DependencyChecker, and DependencyViolation."""

import pytest

from cronwatch.dependency import (
    DependencyChecker,
    DependencyGraph,
    DependencyViolation,
)


@pytest.fixture
def graph() -> DependencyGraph:
    g = DependencyGraph()
    g.register("fetch", [])
    g.register("transform", depends_on=["fetch"])
    g.register("load", depends_on=["fetch", "transform"])
    g.register("report", depends_on=["load"])
    return g


@pytest.fixture
def checker(graph: DependencyGraph) -> DependencyChecker:
    return DependencyChecker(graph)


def test_no_violation_when_deps_met(checker):
    result = checker.check("transform", completed={"fetch"})
    assert result is None


def test_violation_when_dep_missing(checker):
    result = checker.check("transform", completed=set())
    assert isinstance(result, DependencyViolation)
    assert "fetch" in result.missing_deps


def test_violation_lists_all_missing_deps(checker):
    result = checker.check("load", completed=set())
    assert result is not None
    assert set(result.missing_deps) == {"fetch", "transform"}


def test_violation_partial_deps(checker):
    result = checker.check("load", completed={"fetch"})
    assert result is not None
    assert result.missing_deps == ["transform"]


def test_no_violation_for_job_with_no_deps(checker):
    result = checker.check("fetch", completed=set())
    assert result is None


def test_check_all_returns_violations(checker):
    violations = checker.check_all(completed={"fetch"})
    names = [v.job_name for v in violations]
    assert "transform" not in names  # fetch is done
    assert "load" in names           # transform still missing
    assert "report" in names         # load still missing


def test_check_all_empty_when_all_completed(checker):
    completed = {"fetch", "transform", "load", "report"}
    violations = checker.check_all(completed=completed)
    assert violations == []


def test_ready_jobs_no_deps(checker):
    ready = checker.ready_jobs(completed=set())
    assert "fetch" in ready


def test_ready_jobs_after_fetch(checker):
    ready = checker.ready_jobs(completed={"fetch"})
    assert "transform" in ready
    assert "load" not in ready


def test_violation_str_contains_job_name():
    v = DependencyViolation(job_name="load", missing_deps=["fetch"])
    assert "load" in str(v)
    assert "fetch" in str(v)
