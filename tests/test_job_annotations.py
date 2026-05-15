"""Tests for job_annotations module."""
import pytest

from cronwatch.job_metadata import JobMetadata
from cronwatch.job_annotations import (
    AnnotationCriteria,
    AnnotationFilter,
    jobs_with_annotation,
    jobs_with_annotation_value,
)


@pytest.fixture
def metadata() -> JobMetadata:
    m = JobMetadata()
    m.set("job_a", "team", "ops")
    m.set("job_a", "critical", True)
    m.set("job_b", "team", "dev")
    m.set("job_b", "critical", False)
    m.set("job_c", "team", "ops")
    # job_c has no 'critical' annotation
    return m


def test_criteria_matches_key_exists(metadata):
    crit = AnnotationCriteria(key="critical")
    assert crit.matches(metadata, "job_a") is True


def test_criteria_no_match_missing_key(metadata):
    crit = AnnotationCriteria(key="critical")
    assert crit.matches(metadata, "job_c") is False


def test_criteria_matches_exact_value(metadata):
    crit = AnnotationCriteria(key="team", value="ops")
    assert crit.matches(metadata, "job_a") is True
    assert crit.matches(metadata, "job_b") is False


def test_filter_empty_criteria_matches_all(metadata):
    f = AnnotationFilter(metadata)
    result = f.apply(["job_a", "job_b", "job_c"])
    assert result == ["job_a", "job_b", "job_c"]


def test_filter_single_criterion(metadata):
    f = AnnotationFilter(metadata).add_criterion("team", "ops")
    result = f.apply(["job_a", "job_b", "job_c"])
    assert result == ["job_a", "job_c"]


def test_filter_multiple_criteria(metadata):
    f = AnnotationFilter(metadata)
    f.add_criterion("team", "ops")
    f.add_criterion("critical", True)
    result = f.apply(["job_a", "job_b", "job_c"])
    assert result == ["job_a"]


def test_filter_excluded(metadata):
    f = AnnotationFilter(metadata).add_criterion("team", "dev")
    excluded = f.excluded(["job_a", "job_b", "job_c"])
    assert "job_a" in excluded
    assert "job_c" in excluded
    assert "job_b" not in excluded


def test_jobs_with_annotation(metadata):
    result = jobs_with_annotation(metadata, "critical")
    assert set(result) == {"job_a", "job_b"}


def test_jobs_with_annotation_value(metadata):
    result = jobs_with_annotation_value(metadata, "team", "ops")
    assert set(result) == {"job_a", "job_c"}


def test_jobs_with_annotation_value_no_match(metadata):
    result = jobs_with_annotation_value(metadata, "team", "infra")
    assert result == []
