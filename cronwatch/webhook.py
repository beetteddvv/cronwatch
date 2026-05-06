"""Webhook notification backend (HTTP POST)."""

import json
import logging
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class WebhookConfig:
    url: str
    headers: dict[str, str] = field(default_factory=lambda: {"Content-Type": "application/json"})
    timeout: int = 10


class WebhookNotifier:
    def __init__(self, config: WebhookConfig):
        self.config = config

    def send(self, payload: dict[str, Any]) -> bool:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.config.url,
            data=data,
            headers=self.config.headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                status = resp.status
            if 200 <= status < 300:
                logger.info("Webhook delivered to %s (status %d)", self.config.url, status)
                return True
            logger.warning("Webhook returned non-2xx status %d", status)
            return False
        except urllib.error.URLError as exc:
            logger.error("Webhook request failed: %s", exc)
            return False

    def send_alert(self, job_name: str, reason: str, details: str = "") -> bool:
        payload = {
            "source": "cronwatch",
            "job": job_name,
            "reason": reason,
            "details": details,
        }
        return self.send(payload)
