"""Tests for the Dispatcher routing layer."""

from unittest.mock import MagicMock, patch
import pytest
from cronwatch.alerts import AlertEvent
from cronwatch.dispatch import Dispatcher


@pytest.fixture
def email_alert_config():
    cfg = MagicMock()
    cfg.method = "email"
    cfg.smtp_host = "smtp.example.com"
    cfg.smtp_port = 587
    cfg.smtp_user = None
    cfg.smtp_password = None
    cfg.recipients = ["ops@example.com"]
    cfg.webhook_url = None
    return cfg


@pytest.fixture
def webhook_alert_config():
    cfg = MagicMock()
    cfg.method = "webhook"
    cfg.webhook_url = "https://hooks.example.com/cronwatch"
    cfg.smtp_host = None
    cfg.recipients = []
    return cfg


@pytest.fixture
def sample_event():
    return AlertEvent(job_name="backup", reason="missed", details="Expected at 02:00")


def test_dispatch_email_calls_send_batch(email_alert_config, sample_event):
    dispatcher = Dispatcher(email_alert_config)
    with patch.object(dispatcher._email, "send_batch", return_value={"ops@example.com": True}) as mock_batch:
        result = dispatcher.dispatch(sample_event)
    assert result is True
    mock_batch.assert_called_once()


def test_dispatch_webhook_calls_send_alert(webhook_alert_config, sample_event):
    dispatcher = Dispatcher(webhook_alert_config)
    with patch.object(dispatcher._webhook, "send_alert", return_value=True) as mock_send:
        result = dispatcher.dispatch(sample_event)
    assert result is True
    mock_send.assert_called_once_with(
        job_name="backup", reason="missed", details="Expected at 02:00"
    )


def test_dispatch_unknown_method_returns_false(sample_event):
    cfg = MagicMock()
    cfg.method = "slack"
    cfg.smtp_host = None
    cfg.webhook_url = None
    dispatcher = Dispatcher(cfg)
    result = dispatcher.dispatch(sample_event)
    assert result is False
