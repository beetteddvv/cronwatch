"""Tests for cronwatch.job_grouping."""

import pytest
from cronwatch.job_grouping import JobGroup, JobGroupManager, GroupStatus


@pytest.fixture
def manager() -> JobGroupManager:
    return JobGroupManager()


# --- JobGroup ---

def test_job_group_add():
    grp = JobGroup(name="ops")
    grp.add("backup")
    assert "backup" in grp


def test_job_group_add_deduplicates():
    grp = JobGroup(name="ops")
    grp.add("backup")
    grp.add("backup")
    assert len(grp) == 1


def test_job_group_remove():
    grp = JobGroup(name="ops")
    grp.add("backup")
    grp.remove("backup")
    assert "backup" not in grp


def test_job_group_len():
    grp = JobGroup(name="ops")
    grp.add("a")
    grp.add("b")
    assert len(grp) == 2


# --- JobGroupManager ---

def test_create_group_returns_group(manager):
    grp = manager.create_group("ops")
    assert isinstance(grp, JobGroup)
    assert grp.name == "ops"


def test_create_group_idempotent(manager):
    g1 = manager.create_group("ops")
    g2 = manager.create_group("ops")
    assert g1 is g2


def test_add_job_creates_group_if_missing(manager):
    manager.add_job("infra", "sync")
    assert "infra" in manager.all_groups()


def test_add_job_places_job_in_group(manager):
    manager.add_job("infra", "sync")
    grp = manager.get_group("infra")
    assert "sync" in grp


def test_get_group_returns_none_for_missing(manager):
    assert manager.get_group("nope") is None


def test_groups_for_job_returns_all_groups(manager):
    manager.add_job("ops", "backup")
    manager.add_job("infra", "backup")
    groups = manager.groups_for_job("backup")
    assert set(groups) == {"ops", "infra"}


def test_groups_for_job_empty_when_not_member(manager):
    manager.create_group("ops")
    assert manager.groups_for_job("orphan") == []


def test_all_groups_lists_created_groups(manager):
    manager.create_group("a")
    manager.create_group("b")
    assert set(manager.all_groups()) == {"a", "b"}


# --- GroupStatus ---

def test_status_returns_none_for_missing_group(manager):
    assert manager.status("ghost", []) is None


def test_status_all_healthy(manager):
    manager.add_job("ops", "job1")
    manager.add_job("ops", "job2")
    s = manager.status("ops", [])
    assert s.total == 2
    assert s.healthy == 2
    assert s.failing == 0
    assert s.all_healthy is True


def test_status_some_failing(manager):
    manager.add_job("ops", "job1")
    manager.add_job("ops", "job2")
    s = manager.status("ops", ["job1"])
    assert s.failing == 1
    assert s.healthy == 1
    assert s.all_healthy is False


def test_status_health_ratio(manager):
    manager.add_job("ops", "job1")
    manager.add_job("ops", "job2")
    manager.add_job("ops", "job3")
    manager.add_job("ops", "job4")
    s = manager.status("ops", ["job1"])
    assert s.health_ratio == pytest.approx(0.75)


def test_status_empty_group_health_ratio_is_one(manager):
    manager.create_group("empty")
    s = manager.status("empty", [])
    assert s.health_ratio == 1.0
