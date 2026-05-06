"""Tests for EmailNotifier."""

import smtplib
from unittest.mock import MagicMock, patch
import pytest
from cronwatch.notifier import EmailNotifier, SmtpConfig


@pytest.fixture
def smtp_config():
    return SmtpConfig(host="smtp.example.com", port=587, use_tls=True)


@pytest.fixture
def notifier(smtp_config):
    return EmailNotifier(smtp_config)


def test_send_returns_true_on_success(notifier):
    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server
        result = notifier.send("user@example.com", "Test Subject", "Test body")
    assert result is True
    mock_server.sendmail.assert_called_once()


def test_send_returns_false_on_smtp_error(notifier):
    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_smtp_cls.side_effect = smtplib.SMTPException("connection refused")
        result = notifier.send("user@example.com", "Subject", "Body")
    assert result is False


def test_send_returns_false_on_os_error(notifier):
    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_smtp_cls.side_effect = OSError("network unreachable")
        result = notifier.send("user@example.com", "Subject", "Body")
    assert result is False


def test_send_uses_tls_when_configured(notifier):
    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server
        notifier.send("a@b.com", "s", "b")
    mock_server.starttls.assert_called_once()


def test_send_batch_returns_dict(notifier):
    with patch.object(notifier, "send", return_value=True):
        result = notifier.send_batch(["a@x.com", "b@x.com"], "S", "B")
    assert result == {"a@x.com": True, "b@x.com": True}
