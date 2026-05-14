"""Tests for cronwatch.tag_filter."""

from dataclasses import dataclass, field
from typing import List

import pytest

from cronwatch.tag_filter import TagFilter, TagFilterManager


@dataclass
class FakeJob:
    name: str
    tags: List[str] = field(default_factory=list)


# ── TagFilter.matches ──────────────────────────────────────────────────────────

def test_matches_empty_filter_always_true():
    tf = TagFilter()
    assert tf.matches(["critical", "nightly"]) is True


def test_matches_include_hit():
    tf = TagFilter(include=["critical"])
    assert tf.matches(["critical", "nightly"]) is True


def test_matches_include_miss():
    tf = TagFilter(include=["critical"])
    assert tf.matches(["nightly"]) is False


def test_matches_exclude_hit():
    tf = TagFilter(exclude=["disabled"])
    assert tf.matches(["critical", "disabled"]) is False


def test_matches_exclude_miss():
    tf = TagFilter(exclude=["disabled"])
    assert tf.matches(["critical"]) is True


def test_matches_include_and_exclude_combined():
    tf = TagFilter(include=["critical"], exclude=["disabled"])
    assert tf.matches(["critical"]) is True
    assert tf.matches(["critical", "disabled"]) is False
    assert tf.matches(["nightly"]) is False


# ── TagFilterManager.filter_jobs ───────────────────────────────────────────────

@pytest.fixture
def jobs():
    return [
        FakeJob("job_a", tags=["critical", "nightly"]),
        FakeJob("job_b", tags=["nightly"]),
        FakeJob("job_c", tags=["disabled"]),
        FakeJob("job_d"),  # no tags
    ]


def test_filter_jobs_empty_filter_returns_all(jobs):
    mgr = TagFilterManager()
    assert mgr.filter_jobs(jobs) == jobs


def test_filter_jobs_include_only(jobs):
    mgr = TagFilterManager(TagFilter(include=["critical"]))
    result = mgr.filter_jobs(jobs)
    assert len(result) == 1
    assert result[0].name == "job_a"


def test_filter_jobs_exclude_only(jobs):
    mgr = TagFilterManager(TagFilter(exclude=["disabled"]))
    names = [j.name for j in mgr.filter_jobs(jobs)]
    assert "job_c" not in names
    assert "job_a" in names


def test_filter_jobs_no_tags_attribute(jobs):
    mgr = TagFilterManager(TagFilter(include=["critical"]))
    result = mgr.filter_jobs(jobs)
    # job_d has no tags — should not appear
    assert all(j.name != "job_d" for j in result)


def test_active_filter_returns_filter():
    tf = TagFilter(include=["nightly"])
    mgr = TagFilterManager(tf)
    assert mgr.active_filter() is tf
