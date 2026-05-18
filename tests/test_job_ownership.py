"""Tests for job ownership tracking."""

from __future__ import annotations

import pytest

from cronwatch.job_ownership import OwnerRecord, OwnershipRegistry


@pytest.fixture
def registry() -> OwnershipRegistry:
    reg = OwnershipRegistry()
    reg.register(OwnerRecord(job_name="backup", owner="alice", team="ops", contact="alice@example.com"))
    reg.register(OwnerRecord(job_name="report", owner="bob", team="dev"))
    reg.register(OwnerRecord(job_name="cleanup", owner="alice", team="ops"))
    return reg


def test_get_returns_record(registry: OwnershipRegistry) -> None:
    rec = registry.get("backup")
    assert rec is not None
    assert rec.owner == "alice"


def test_get_missing_returns_none(registry: OwnershipRegistry) -> None:
    assert registry.get("nonexistent") is None


def test_jobs_for_owner(registry: OwnershipRegistry) -> None:
    jobs = registry.jobs_for_owner("alice")
    assert set(jobs) == {"backup", "cleanup"}


def test_jobs_for_owner_no_match(registry: OwnershipRegistry) -> None:
    assert registry.jobs_for_owner("charlie") == []


def test_jobs_for_team(registry: OwnershipRegistry) -> None:
    jobs = registry.jobs_for_team("dev")
    assert jobs == ["report"]


def test_all_owners(registry: OwnershipRegistry) -> None:
    assert set(registry.all_owners()) == {"alice", "bob"}


def test_all_teams(registry: OwnershipRegistry) -> None:
    assert set(registry.all_teams()) == {"ops", "dev"}


def test_unowned_jobs(registry: OwnershipRegistry) -> None:
    all_jobs = ["backup", "report", "cleanup", "orphan1", "orphan2"]
    unowned = registry.unowned_jobs(all_jobs)
    assert set(unowned) == {"orphan1", "orphan2"}


def test_unowned_jobs_all_registered(registry: OwnershipRegistry) -> None:
    assert registry.unowned_jobs(["backup", "report", "cleanup"]) == []


def test_owner_record_roundtrip() -> None:
    rec = OwnerRecord(job_name="sync", owner="dave", team="infra", contact="dave@example.com")
    restored = OwnerRecord.from_dict(rec.to_dict())
    assert restored.job_name == rec.job_name
    assert restored.owner == rec.owner
    assert restored.team == rec.team
    assert restored.contact == rec.contact


def test_owner_record_to_dict_keys() -> None:
    rec = OwnerRecord(job_name="job", owner="eve")
    d = rec.to_dict()
    assert set(d.keys()) == {"job_name", "owner", "team", "contact"}


def test_register_overwrites_existing() -> None:
    reg = OwnershipRegistry()
    reg.register(OwnerRecord(job_name="job", owner="old"))
    reg.register(OwnerRecord(job_name="job", owner="new"))
    assert reg.get("job").owner == "new"
