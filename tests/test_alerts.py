import pytest
from unittest.mock import MagicMock, patch

from cronwatch.alerts import AlertEvent, AlertManager
from cronwatch.config import AlertConfig


@pytest.fixture
def log_alert_config():
    return AlertConfig(method="log", recipients=[])


@pytest.fixture
def email_alert_config():
    return AlertConfig(
        method="email",
        smtp_host="smtp.example.com",
        smtp_port=25,
        sender="cron@example.com",
        recipients=["ops@example.com"],
    )


@pytest.fixture
def sample_event():
    return AlertEvent(
        job_name="backup",
        event_type="missed",
        message="Job has not run in 2 hours",
    )


def test_send_log_returns_true(log_alert_config, sample_event):
    manager = AlertManager(log_alert_config)
    result = manager.send(sample_event)
    assert result is True


def test_send_unknown_method_returns_false(sample_event):
    config = AlertConfig(method="slack", recipients=[])
    manager = AlertManager(config)
    assert manager.send(sample_event) is False


def test_build_body_includes_job_name(log_alert_config, sample_event):
    manager = AlertManager(log_alert_config)
    body = manager._build_body(sample_event)
    assert "backup" in body
    assert "missed" in body


def test_build_body_includes_exit_code():
    config = AlertConfig(method="log", recipients=[])
    event = AlertEvent(job_name="sync", event_type="failure", message="oops", exit_code=1)
    manager = AlertManager(config)
    body = manager._build_body(event)
    assert "Exit code: 1" in body


def test_send_email_success(email_alert_config, sample_event):
    manager = AlertManager(email_alert_config)
    mock_server = MagicMock()
    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.return_value.__enter__.return_value = mock_server
        result = manager.send(sample_event)
    assert result is True
    mock_server.sendmail.assert_called_once()


def test_send_email_missing_host_returns_false(sample_event):
    config = AlertConfig(method="email", smtp_host="", recipients=["a@b.com"])
    manager = AlertManager(config)
    assert manager.send(sample_event) is False


def test_send_email_smtp_error_returns_false(email_alert_config, sample_event):
    manager = AlertManager(email_alert_config)
    with patch("smtplib.SMTP", side_effect=ConnectionRefusedError("refused")):
        result = manager.send(sample_event)
    assert result is False
