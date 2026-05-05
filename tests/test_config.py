"""Tests for cronwatch config loader."""

import os
import pytest
import tempfile
import yaml

from cronwatch.config import load_config, CronwatchConfig, JobConfig, AlertConfig


SAMPLE_CONFIG = {
    "log_file": "/tmp/cronwatch.log",
    "state_dir": "/tmp/cronwatch",
    "check_interval": 30,
    "alerts": {
        "email": "ops@example.com",
        "slack_webhook": "https://hooks.slack.com/test",
    },
    "jobs": [
        {
            "name": "backup",
            "schedule": "0 2 * * *",
            "command": "/usr/local/bin/backup.sh",
            "timeout": 7200,
            "notify": ["email"],
        },
        {
            "name": "cleanup",
            "schedule": "*/15 * * * *",
            "command": "/usr/local/bin/cleanup.sh",
            "alert_on_missed": False,
        },
    ],
}


@pytest.fixture
def config_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(SAMPLE_CONFIG, f)
        path = f.name
    yield path
    os.unlink(path)


def test_load_config_returns_correct_type(config_file):
    cfg = load_config(config_file)
    assert isinstance(cfg, CronwatchConfig)


def test_load_config_jobs(config_file):
    cfg = load_config(config_file)
    assert len(cfg.jobs) == 2
    assert all(isinstance(j, JobConfig) for j in cfg.jobs)


def test_load_config_job_fields(config_file):
    cfg = load_config(config_file)
    backup = cfg.jobs[0]
    assert backup.name == "backup"
    assert backup.schedule == "0 2 * * *"
    assert backup.timeout == 7200
    assert backup.notify == ["email"]
    assert backup.alert_on_failure is True


def test_load_config_job_defaults(config_file):
    cfg = load_config(config_file)
    cleanup = cfg.jobs[1]
    assert cleanup.timeout == 3600
    assert cleanup.alert_on_missed is False
    assert cleanup.notify == []


def test_load_config_alerts(config_file):
    cfg = load_config(config_file)
    assert isinstance(cfg.alerts, AlertConfig)
    assert cfg.alerts.email == "ops@example.com"
    assert cfg.alerts.slack_webhook == "https://hooks.slack.com/test"
    assert cfg.alerts.pagerduty_key is None


def test_load_config_top_level_fields(config_file):
    cfg = load_config(config_file)
    assert cfg.log_file == "/tmp/cronwatch.log"
    assert cfg.check_interval == 30


def test_load_config_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path/config.yaml")


def test_load_config_invalid_yaml():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("- just\n- a list\n")
        path = f.name
    try:
        with pytest.raises(ValueError, match="must be a YAML mapping"):
            load_config(path)
    finally:
        os.unlink(path)
