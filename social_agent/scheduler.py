from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Iterable, Mapping

from .config_loader import PostDefinition
from .platform_clients import PlatformClient

logger = logging.getLogger(__name__)


class Scheduler:
    """Dispatch posts at their scheduled times using provided clients."""

    def __init__(self, clients: Mapping[str, PlatformClient], simulate: bool = False) -> None:
        self._clients = clients
        self._simulate = simulate
        self._timers: list[threading.Timer] = []

    def _dispatch(self, post: PostDefinition) -> None:
        client = self._clients.get(post.platform)
        if not client:
            logger.error("No client configured for platform '%s'", post.platform)
            return

        if self._simulate:
            logger.info("[simulate] would post to %s: %s", post.platform, post.content)
            return

        logger.info("dispatching post to %s", post.platform)
        client.publish(post.content, metadata=post.metadata)

    def schedule_posts(self, posts: Iterable[PostDefinition]) -> None:
        for post in posts:
            now = datetime.now(timezone.utc)
            scheduled_for = post.scheduled_for or now
            delay_seconds = max((scheduled_for - now).total_seconds(), 0)

            if self._simulate:
                logger.info("[simulate] scheduled post for %s at %s (delay=%.2fs)", post.platform, scheduled_for.isoformat(), delay_seconds)
                self._dispatch(post)
                continue

            timer = threading.Timer(delay_seconds, self._dispatch, args=(post,))
            timer.daemon = False
            timer.start()
            self._timers.append(timer)
            logger.info("scheduled post for %s at %s (delay=%.2fs)", post.platform, scheduled_for.isoformat(), delay_seconds)

    def wait(self) -> None:
        for timer in self._timers:
            timer.join()
