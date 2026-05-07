"""Tests for silence window loading from config dicts."""

from datetime import time

import pytest

from cronwatch.silence_loader import load_silence_windows, _parse_time, _parse_days
from cronwatch.silence import SilenceManager


RAW_WINDOWS = [
    {
        "name": "nightly",
        "start": "02:00",
        "end": "04:00",
    },
    {
        "name": "deploy",
        "start": "10:00",
        "end": "10:30",
        "days": ["mon", "wed", "fri"],
        "jobs": ["deploy-prod"],
    },
]


def test_load_returns_silence_manager():
    manager = load_silence_windows(RAW_WINDOWS)
    assert isinstance(manager, SilenceManager)


def test_load_correct_window_count():
    manager = load_silence_windows(RAW_WINDOWS)
    assert len(manager.windows) == 2


def test_load_window_name():
    manager = load_silence_windows(RAW_WINDOWS)
    assert manager.windows[0].name == "nightly"


def test_load_window_times():
    manager = load_silence_windows(RAW_WINDOWS)
    assert manager.windows[0].start == time(2, 0)
    assert manager.windows[0].end == time(4, 0)


def test_load_window_days_from_names():
    manager = load_silence_windows(RAW_WINDOWS)
    assert manager.windows[1].days == [0, 2, 4]


def test_load_window_job_names():
    manager = load_silence_windows(RAW_WINDOWS)
    assert manager.windows[1].job_names == ["deploy-prod"]


def test_load_empty_list():
    manager = load_silence_windows([])
    assert len(manager.windows) == 0


def test_parse_time_valid():
    assert _parse_time("14:30") == time(14, 30)


def test_parse_time_invalid_raises():
    with pytest.raises(ValueError):
        _parse_time("1430")


def test_parse_days_none_returns_all():
    assert _parse_days(None) == list(range(7))


def test_parse_days_int_list():
    assert _parse_days([0, 1, 2]) == [0, 1, 2]
