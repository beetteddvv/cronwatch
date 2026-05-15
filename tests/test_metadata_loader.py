"""Tests for metadata_loader.load_metadata_from_config."""

import pytest

from cronwatch.metadata_loader import load_metadata_from_config


@pytest.fixture
def config_with_metadata():
    return {
        "jobs": [
            {
                "name": "backup",
                "schedule": "0 2 * * *",
                "metadata": {"owner": "ops", "env": "production"},
            },
            {
                "name": "cleanup",
                "schedule": "0 3 * * *",
                "metadata": {"owner": "dev"},
            },
            {
                "name": "report",
                "schedule": "0 6 * * 1",
                # no metadata key
            },
        ]
    }


def test_load_returns_store_with_all_annotated_jobs(config_with_metadata):
    store = load_metadata_from_config(config_with_metadata)
    assert "backup" in store.all_jobs()
    assert "cleanup" in store.all_jobs()


def test_load_correct_annotation_values(config_with_metadata):
    store = load_metadata_from_config(config_with_metadata)
    assert store.get_annotation("backup", "owner") == "ops"
    assert store.get_annotation("backup", "env") == "production"
    assert store.get_annotation("cleanup", "owner") == "dev"


def test_job_without_metadata_not_in_store(config_with_metadata):
    store = load_metadata_from_config(config_with_metadata)
    # 'report' has no metadata block so it should not appear
    assert "report" not in store.all_jobs()


def test_jobs_with_annotation_filters_across_jobs(config_with_metadata):
    store = load_metadata_from_config(config_with_metadata)
    owners = store.jobs_with_annotation("owner")
    assert sorted(owners) == ["backup", "cleanup"]


def test_empty_jobs_list_returns_empty_store():
    store = load_metadata_from_config({"jobs": []})
    assert store.all_jobs() == []


def test_missing_jobs_key_returns_empty_store():
    store = load_metadata_from_config({})
    assert store.all_jobs() == []


def test_job_without_name_is_skipped():
    config = {"jobs": [{"schedule": "* * * * *", "metadata": {"k": "v"}}]}
    store = load_metadata_from_config(config)
    assert store.all_jobs() == []


def test_non_dict_metadata_is_skipped():
    config = {
        "jobs": [
            {"name": "broken", "schedule": "* * * * *", "metadata": "bad-value"}
        ]
    }
    store = load_metadata_from_config(config)
    assert "broken" not in store.all_jobs()
