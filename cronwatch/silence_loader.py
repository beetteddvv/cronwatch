"""Load silence windows from config dict or YAML-compatible structure."""

from datetime import time
from typing import Any

from cronwatch.silence import SilenceWindow, SilenceManager


def _parse_time(value: str) -> time:
    """Parse HH:MM string into a time object."""
    parts = value.strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid time format: {value!r}. Expected HH:MM.")
    return time(int(parts[0]), int(parts[1]))


def _parse_days(value: Any) -> list[int]:
    """Accept a list of ints or day-name strings."""
    day_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3,
               "fri": 4, "sat": 5, "sun": 6}
    if value is None:
        return list(range(7))
    result = []
    for item in value:
        if isinstance(item, int):
            result.append(item)
        else:
            result.append(day_map[str(item).lower()[:3]])
    return result


def load_silence_windows(raw: list[dict]) -> SilenceManager:
    """Build a SilenceManager from a list of raw config dicts."""
    windows = []
    for entry in raw:
        window = SilenceWindow(
            name=entry["name"],
            start=_parse_time(entry["start"]),
            end=_parse_time(entry["end"]),
            days=_parse_days(entry.get("days")),
            job_names=entry.get("jobs"),
        )
        windows.append(window)
    return SilenceManager(windows)
