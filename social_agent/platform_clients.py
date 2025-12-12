from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Protocol

logger = logging.getLogger(__name__)


class PlatformClient(Protocol):
    """Client that can publish a piece of content to a platform."""

    def publish(self, content: str, metadata: Mapping[str, Any] | None = None) -> None:
        ...


@dataclass
class ConsoleClient:
    """Client that prints content to the console.

    This client is useful for local demos or unit tests because it does
    not make any outbound network calls.
    """

    label: str = "console"

    def publish(self, content: str, metadata: Mapping[str, Any] | None = None) -> None:  # type: ignore[override]
        formatted = json.dumps({"label": self.label, "content": content, "metadata": metadata}, ensure_ascii=False)
        logger.info("[console] %s", formatted)


@dataclass
class WebhookClient:
    """Client that POSTs content to a generic webhook endpoint."""

    url: str
    headers: Mapping[str, str] | None = None
    timeout: float = 10

    def publish(self, content: str, metadata: Mapping[str, Any] | None = None) -> None:  # type: ignore[override]
        payload = {"content": content, "metadata": metadata or {}}
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(self.url, data=data, headers={"Content-Type": "application/json", **(self.headers or {})})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                logger.info("[webhook] status=%s url=%s", response.status, self.url)
        except urllib.error.URLError as exc:  # pragma: no cover - external dependency
            logger.error("[webhook] failed to post url=%s error=%s", self.url, exc)


def create_client(name: str, settings: Mapping[str, Any]) -> PlatformClient:
    """Instantiate a client by name using configuration settings.

    The configuration may declare a ``type`` field to allow multiple clients of
    the same underlying type (for example, different webhooks) to coexist under
    distinct names such as ``facebook`` or ``instagram``.
    """

    client_type = str(settings.get("type", name))

    if client_type == "console":
        label = str(settings.get("label", name))
        return ConsoleClient(label=label)

    if client_type == "webhook":
        url = settings.get("url")
        if not url:
            raise ValueError("webhook client requires a 'url' field")
        headers_setting = settings.get("headers")
        headers: Dict[str, str] = {}
        if isinstance(headers_setting, Mapping):
            headers = {str(key): str(value) for key, value in headers_setting.items()}
        timeout = float(settings.get("timeout", 10))
        return WebhookClient(url=str(url), headers=headers or None, timeout=timeout)

    raise ValueError(f"Unknown client type: {client_type}")
