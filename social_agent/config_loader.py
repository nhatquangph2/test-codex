from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional


@dataclass
class PostDefinition:
    platform: str
    content: str
    scheduled_for: Optional[datetime] = None
    metadata: Mapping[str, Any] | None = None


@dataclass
class AgentConfig:
    platform_settings: Mapping[str, Mapping[str, Any]]
    posts: Iterable[PostDefinition]


ISO_FORMAT_HINT = "YYYY-MM-DDTHH:MM:SSZ"


def parse_datetime(raw_value: str) -> datetime:
    """Parse an ISO-like timestamp into an aware datetime.

    The function accepts trailing ``Z`` to indicate UTC and ensures the
    resulting datetime is timezone-aware.
    """

    normalized = raw_value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:  # pragma: no cover - defensive branch
        raise ValueError(f"Invalid datetime format (expected {ISO_FORMAT_HINT}): {raw_value}") from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_config(path: str | Path) -> AgentConfig:
    """Load an AgentConfig from a JSON file."""

    with Path(path).open("r", encoding="utf-8") as handle:
        raw = json.load(handle)

    platform_settings = raw.get("platform_settings", {})
    if not isinstance(platform_settings, Mapping):
        raise ValueError("'platform_settings' must be an object")

    raw_posts = raw.get("posts", [])
    if not isinstance(raw_posts, list):
        raise ValueError("'posts' must be a list")

    posts: List[PostDefinition] = []
    for entry in raw_posts:
        if not isinstance(entry, Mapping):
            raise ValueError("each post must be an object")

        content = entry.get("content")
        platform = entry.get("platform")
        if not content or not platform:
            raise ValueError("each post requires 'content' and 'platform' fields")

        scheduled_for_raw = entry.get("scheduled_for")
        scheduled_for = parse_datetime(scheduled_for_raw) if isinstance(scheduled_for_raw, str) else None
        metadata = entry.get("metadata") if isinstance(entry.get("metadata"), Mapping) else None

        posts.append(
            PostDefinition(
                platform=str(platform),
                content=str(content),
                scheduled_for=scheduled_for,
                metadata=metadata,
            )
        )

    return AgentConfig(platform_settings=platform_settings, posts=posts)
