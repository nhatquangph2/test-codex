from __future__ import annotations

from datetime import datetime, timezone
from textwrap import shorten
from typing import Iterable, Mapping

from .config_loader import AgentConfig, PostDefinition


def _format_timestamp(value: datetime | None) -> str:
    if value is None:
        return "ngay lập tức"
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _describe_client(name: str, settings: Mapping[str, object]) -> str:
    client_type = str(settings.get("type", name))
    summary_bits = [f"type={client_type}"]

    if client_type == "webhook":
        url = settings.get("url")
        if url:
            summary_bits.append(f"url={url}")
        timeout = settings.get("timeout")
        if timeout:
            summary_bits.append(f"timeout={timeout}s")

    label = settings.get("label")
    if label:
        summary_bits.append(f"label={label}")

    return f"- {name} ({', '.join(summary_bits)})"


def _describe_post(post: PostDefinition) -> str:
    timestamp = _format_timestamp(post.scheduled_for)
    content_preview = shorten(post.content, width=80, placeholder="…")
    return f"- [{post.platform}] {content_preview} @ {timestamp}"


def render_preview(config: AgentConfig) -> str:
    """Render a human-readable preview of configured clients and posts."""

    lines: list[str] = []

    lines.append("Cấu hình client:")
    if not config.platform_settings:
        lines.append("(không có client nào; thêm mục 'platform_settings' để cấu hình)")
    else:
        for name, settings in config.platform_settings.items():
            lines.append(_describe_client(name, settings))

    lines.append("\nBài đăng sắp chạy:")
    posts: Iterable[PostDefinition] = config.posts or []
    has_posts = False
    for post in posts:
        has_posts = True
        lines.append(_describe_post(post))

    if not has_posts:
        lines.append("(chưa có bài đăng nào trong danh sách 'posts')")

    return "\n".join(lines)
