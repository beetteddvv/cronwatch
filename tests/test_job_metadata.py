"""Tests for JobMetadata and JobMetadataStore."""

import pytest

from cronwatch.job_metadata import JobMetadata, JobMetadataStore


# ---------------------------------------------------------------------------
# JobMetadata unit tests
# ---------------------------------------------------------------------------

def test_set_and_get_annotation():
    meta = JobMetadata(job_name="backup")
    meta.set("owner", "ops")
    assert meta.get("owner") == "ops"


def test_get_missing_key_returns_default():
    meta = JobMetadata(job_name="backup")
    assert meta.get("missing", "fallback") == "fallback"


def test_remove_existing_key_returns_true():
    meta = JobMetadata(job_name="backup")
    meta.set("owner", "ops")
    assert meta.remove("owner") is True
    assert meta.get("owner") is None


def test_remove_missing_key_returns_false():
    meta = JobMetadata(job_name="backup")
    assert meta.remove("nonexistent") is False


def test_keys_returns_annotation_names():
    meta = JobMetadata(job_name="backup")
    meta.set("a", 1)
    meta.set("b", 2)
    assert sorted(meta.keys()) == ["a", "b"]


def test_to_dict_roundtrip():
    meta = JobMetadata(job_name="backup")
    meta.set("owner", "ops")
    meta.set("env", "prod")
    restored = JobMetadata.from_dict(meta.to_dict())
    assert restored.job_name == "backup"
    assert restored.get("owner") == "ops"
    assert restored.get("env") == "prod"


# ---------------------------------------------------------------------------
# JobMetadataStore unit tests
# ---------------------------------------------------------------------------

@pytest.fixture
def store() -> JobMetadataStore:
    return JobMetadataStore()


def test_annotate_creates_entry(store):
    store.annotate("backup", "owner", "ops")
    assert store.get_annotation("backup", "owner") == "ops"


def test_get_annotation_missing_job_returns_default(store):
    assert store.get_annotation("ghost", "owner", "nobody") == "nobody"


def test_get_metadata_returns_none_for_unknown_job(store):
    assert store.get_metadata("ghost") is None


def test_get_metadata_returns_object_after_annotate(store):
    store.annotate("backup", "env", "prod")
    meta = store.get_metadata("backup")
    assert meta is not None
    assert meta.job_name == "backup"


def test_remove_annotation_true_when_exists(store):
    store.annotate("backup", "owner", "ops")
    assert store.remove_annotation("backup", "owner") is True


def test_remove_annotation_false_for_unknown_job(store):
    assert store.remove_annotation("ghost", "owner") is False


def test_all_jobs_returns_annotated_names(store):
    store.annotate("backup", "k", "v")
    store.annotate("cleanup", "k", "v")
    assert sorted(store.all_jobs()) == ["backup", "cleanup"]


def test_jobs_with_annotation_filters_correctly(store):
    store.annotate("backup", "owner", "ops")
    store.annotate("cleanup", "env", "dev")
    store.annotate("report", "owner", "dev-team")
    result = store.jobs_with_annotation("owner")
    assert sorted(result) == ["backup", "report"]
