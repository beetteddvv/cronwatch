"""Tests for cronwatch.label_router."""

from unittest.mock import MagicMock, patch
import pytest

from cronwatch.alerts import AlertEvent
from cronwatch.label_router import LabelRouter, RoutingRule


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_event():
    return AlertEvent(
        job_name="nightly-backup",
        message="Job did not run",
        severity="critical",
    )


def _make_dispatcher():
    d = MagicMock()
    d.dispatch = MagicMock()
    return d


@pytest.fixture()
def ops_dispatcher():
    return _make_dispatcher()


@pytest.fixture()
def dev_dispatcher():
    return _make_dispatcher()


@pytest.fixture()
def router(ops_dispatcher, dev_dispatcher):
    rules = [
        RoutingRule(label_key="team", label_value="ops", target="ops"),
        RoutingRule(label_key="team", label_value="dev", target="dev"),
    ]
    dispatchers = {"ops": ops_dispatcher, "dev": dev_dispatcher}
    return LabelRouter(rules=rules, dispatchers=dispatchers, default_target=None)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_route_matching_label_calls_correct_dispatcher(router, ops_dispatcher, dev_dispatcher, sample_event):
    result = router.route(sample_event, labels={"team": "ops"})
    assert result is True
    ops_dispatcher.dispatch.assert_called_once_with(sample_event)
    dev_dispatcher.dispatch.assert_not_called()


def test_route_dev_label_calls_dev_dispatcher(router, ops_dispatcher, dev_dispatcher, sample_event):
    result = router.route(sample_event, labels={"team": "dev"})
    assert result is True
    dev_dispatcher.dispatch.assert_called_once_with(sample_event)
    ops_dispatcher.dispatch.assert_not_called()


def test_route_no_match_no_default_returns_false(router, sample_event):
    result = router.route(sample_event, labels={"team": "qa"})
    assert result is False


def test_unrouted_count_increments_on_miss(router, sample_event):
    router.route(sample_event, labels={"team": "unknown"})
    router.route(sample_event, labels={})
    assert router.unrouted_count == 2


def test_route_uses_default_target_when_no_rule_matches(ops_dispatcher, dev_dispatcher, sample_event):
    rules = [RoutingRule(label_key="team", label_value="ops", target="ops")]
    dispatchers = {"ops": ops_dispatcher, "default": dev_dispatcher}
    router = LabelRouter(rules=rules, dispatchers=dispatchers, default_target="default")

    result = router.route(sample_event, labels={"team": "qa"})
    assert result is True
    dev_dispatcher.dispatch.assert_called_once_with(sample_event)


def test_route_missing_dispatcher_target_returns_false(sample_event):
    rules = [RoutingRule(label_key="env", label_value="prod", target="missing")]
    router = LabelRouter(rules=rules, dispatchers={}, default_target=None)
    result = router.route(sample_event, labels={"env": "prod"})
    assert result is False
    assert router.unrouted_count == 1


def test_registered_targets_returns_all_keys(router):
    targets = router.registered_targets()
    assert set(targets) == {"ops", "dev"}


def test_route_none_labels_treated_as_empty(router, sample_event):
    result = router.route(sample_event, labels=None)
    assert result is False
