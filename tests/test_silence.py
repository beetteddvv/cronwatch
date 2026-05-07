"""Tests for SilenceWindow and SilenceManager."""

from datetime import datetime, time

import pytest

from cronwatch.silence import SilenceWindow, SilenceManager


@pytest.fixture
def daily_window():
    return SilenceWindow(
        name="nightly",
        start=time(2, 0),
        end=time(4, 0),
    )


@pytest.fixture
def job_specific_window():
    return SilenceWindow(
        name="deploy",
        start=time(10, 0),
        end=time(10, 30),
        job_names=["deploy-job"],
    )


def _dt(hour: int, minute: int = 0, weekday: int = 0) -> datetime:
    """Create a datetime on a Monday by default."""
    # 2024-01-01 is a Monday
    from datetime import date, timedelta
    base = datetime(2024, 1, 1)  # Monday
    delta = timedelta(days=weekday)
    return (base + delta).replace(hour=hour, minute=minute)


def test_covers_inside_window(daily_window):
    assert daily_window.covers("any-job", _dt(3, 0)) is True


def test_covers_outside_window(daily_window):
    assert daily_window.covers("any-job", _dt(5, 0)) is False


def test_covers_boundary_start(daily_window):
    assert daily_window.covers("any-job", _dt(2, 0)) is True


def test_covers_wrong_day():
    window = SilenceWindow(name="weekdays", start=time(1, 0), end=time(2, 0), days=[0, 1, 2, 3, 4])
    saturday = _dt(1, 30, weekday=5)
    assert window.covers("job", saturday) is False


def test_covers_overnight_window():
    window = SilenceWindow(name="overnight", start=time(23, 0), end=time(1, 0))
    assert window.covers("job", _dt(23, 30)) is True
    assert window.covers("job", _dt(0, 30)) is True
    assert window.covers("job", _dt(2, 0)) is False


def test_covers_job_specific_match(job_specific_window):
    assert job_specific_window.covers("deploy-job", _dt(10, 15)) is True


def test_covers_job_specific_no_match(job_specific_window):
    assert job_specific_window.covers("other-job", _dt(10, 15)) is False


def test_silence_manager_is_silenced():
    window = SilenceWindow(name="w", start=time(3, 0), end=time(5, 0))
    manager = SilenceManager([window])
    assert manager.is_silenced("any", _dt(4, 0)) is True
    assert manager.is_silenced("any", _dt(6, 0)) is False


def test_silence_manager_empty_returns_false():
    manager = SilenceManager()
    assert manager.is_silenced("job", _dt(12, 0)) is False


def test_silence_manager_add_window():
    manager = SilenceManager()
    manager.add_window(SilenceWindow(name="w", start=time(0, 0), end=time(23, 59)))
    assert manager.is_silenced("job", _dt(12, 0)) is True
