"""Configuration loader for cronwatch."""

import os
import yaml
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class JobConfig:
    name: str
    schedule: str
    command: str
    timeout: int = 3600
    alert_on_failure: bool = True
    alert_on_missed: bool = True
    notify: List[str] = field(default_factory=list)


@dataclass
class AlertConfig:
    email: Optional[str] = None
    slack_webhook: Optional[str] = None
    pagerduty_key: Optional[str] = None


@dataclass
class CronwatchConfig:
    jobs: List[JobConfig] = field(default_factory=list)
    alerts: AlertConfig = field(default_factory=AlertConfig)
    log_file: str = "/var/log/cronwatch.log"
    state_dir: str = "/var/lib/cronwatch"
    check_interval: int = 60


def load_config(path: str) -> CronwatchConfig:
    """Load and parse a YAML config file into a CronwatchConfig object."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict):
        raise ValueError("Config file must be a YAML mapping")

    jobs = [
        JobConfig(
            name=j["name"],
            schedule=j["schedule"],
            command=j["command"],
            timeout=j.get("timeout", 3600),
            alert_on_failure=j.get("alert_on_failure", True),
            alert_on_missed=j.get("alert_on_missed", True),
            notify=j.get("notify", []),
        )
        for j in raw.get("jobs", [])
    ]

    raw_alerts = raw.get("alerts", {})
    alerts = AlertConfig(
        email=raw_alerts.get("email"),
        slack_webhook=raw_alerts.get("slack_webhook"),
        pagerduty_key=raw_alerts.get("pagerduty_key"),
    )

    return CronwatchConfig(
        jobs=jobs,
        alerts=alerts,
        log_file=raw.get("log_file", "/var/log/cronwatch.log"),
        state_dir=raw.get("state_dir", "/var/lib/cronwatch"),
        check_interval=raw.get("check_interval", 60),
    )
