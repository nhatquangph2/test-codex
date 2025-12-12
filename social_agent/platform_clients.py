"""Platform-specific client implementations for social media posting."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Dict, Tuple


class SocialClientError(RuntimeError):
    """Raised when an API call fails or a client is misconfigured."""


class HttpResponse:
    """Minimal HTTP response wrapper for JSON APIs."""

    def __init__(self, status_code: int, text: str):
        self.status_code = status_code
        self.text = text

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 400

    def json(self) -> Dict:
        return json.loads(self.text)


class SimpleSession:
    """Lightweight HTTP session using urllib to avoid extra dependencies."""

    def post(
        self, url: str, json_payload: Dict | None = None, headers: Dict | None = None
    ) -> HttpResponse:
        payload = json.dumps(json_payload).encode("utf-8") if json_payload is not None else None
        headers = headers or {}
        if payload and "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(url, data=payload, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(request) as resp:  # pragma: no cover - exercised via mocks
                body = resp.read().decode("utf-8")
                return HttpResponse(status_code=resp.getcode(), text=body)
        except urllib.error.HTTPError as exc:  # pragma: no cover - defensive
            body = exc.read().decode("utf-8") if exc.fp else str(exc)
            return HttpResponse(status_code=exc.code, text=body)


@dataclass
class BaseClient:
    """Base class for platform clients."""

    platform: str
    endpoint: str
    access_token: str
    session: SimpleSession = field(default_factory=SimpleSession)
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger(__name__))

    def build_request(self, content: Dict) -> Tuple[Dict, Dict]:  # pragma: no cover - interface
        raise NotImplementedError

    def publish(self, content: Dict) -> Dict:
        payload, headers = self.build_request(content)
        response = self.session.post(self.endpoint, json_payload=payload, headers=headers)
        return self._handle_response(response)

    def _handle_response(self, response: HttpResponse) -> Dict:
        if response.status_code == 401:
            self.logger.error("%s token expired: %s", self.platform, response.text)
            raise SocialClientError(f"{self.platform} token expired: {response.text}")

        if not response.ok:
            self.logger.error(
                "%s API error (%s): %s", self.platform, response.status_code, response.text
            )
            raise SocialClientError(
                f"{self.platform} API error ({response.status_code}): {response.text}"
            )

        try:
            return response.json()
        except ValueError as exc:  # pragma: no cover - defensive
            self.logger.error("%s returned non-JSON response: %s", self.platform, response.text)
            raise SocialClientError("Invalid JSON response") from exc


class FacebookClient(BaseClient):
    """Client for posting to Facebook Pages."""

    def __init__(self, page_id: str, access_token: str):
        endpoint = f"https://graph.facebook.com/v18.0/{page_id}/feed"
        super().__init__(platform="facebook", endpoint=endpoint, access_token=access_token)

    def build_request(self, content: Dict) -> Tuple[Dict, Dict]:
        payload = {"message": content["message"], "access_token": self.access_token}
        if content.get("link"):
            payload["link"] = content["link"]
        return payload, {}


class InstagramClient(BaseClient):
    """Client for posting to Instagram via the Graph API."""

    def __init__(self, business_account_id: str, access_token: str):
        endpoint = f"https://graph.facebook.com/v18.0/{business_account_id}/media"
        super().__init__(platform="instagram", endpoint=endpoint, access_token=access_token)

    def build_request(self, content: Dict) -> Tuple[Dict, Dict]:
        payload = {
            "image_url": content["image_url"],
            "caption": content.get("caption", ""),
            "access_token": self.access_token,
        }
        return payload, {}


class TikTokClient(BaseClient):
    """Client for posting to TikTok with the Business API."""

    def __init__(self, advertiser_id: str, access_token: str):
        endpoint = "https://open.tiktokapis.com/v2/post/publish/"
        super().__init__(platform="tiktok", endpoint=endpoint, access_token=access_token)
        self.advertiser_id = advertiser_id

    def build_request(self, content: Dict) -> Tuple[Dict, Dict]:
        payload = {
            "post_info": {
                "advertiser_id": self.advertiser_id,
                "caption": content["caption"],
            },
            "source_info": {"source": "PULL_FROM_URL", "video_url": content["video_url"]},
        }
        headers = {"Authorization": f"Bearer {self.access_token}"}
        return payload, headers


class YouTubeClient(BaseClient):
    """Client for uploading videos to YouTube."""

    def __init__(self, channel_id: str, access_token: str):
        endpoint = "https://www.googleapis.com/youtube/v3/videos?part=snippet,status"
        super().__init__(platform="youtube", endpoint=endpoint, access_token=access_token)
        self.channel_id = channel_id

    def build_request(self, content: Dict) -> Tuple[Dict, Dict]:
        payload = {
            "snippet": {
                "title": content["title"],
                "description": content.get("description", ""),
                "categoryId": content.get("category_id", "22"),
            },
            "status": {
                "privacyStatus": content.get("privacy_status", "private"),
                "selfDeclaredMadeForKids": content.get("made_for_kids", False),
            },
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Upload-Content-ChannelId": self.channel_id,
        }
        return payload, headers


def create_client(config: Dict) -> BaseClient:
    """Create a platform client from a configuration mapping."""

    if "type" not in config:
        raise ValueError("Missing required field: type")

    platform = config["type"].lower()
    mappings = {
        "facebook": {
            "required": ["page_id", "access_token"],
            "factory": lambda cfg: FacebookClient(cfg["page_id"], cfg["access_token"]),
        },
        "instagram": {
            "required": ["business_account_id", "access_token"],
            "factory": lambda cfg: InstagramClient(
                cfg["business_account_id"], cfg["access_token"]
            ),
        },
        "tiktok": {
            "required": ["advertiser_id", "access_token"],
            "factory": lambda cfg: TikTokClient(cfg["advertiser_id"], cfg["access_token"]),
        },
        "youtube": {
            "required": ["channel_id", "access_token"],
            "factory": lambda cfg: YouTubeClient(cfg["channel_id"], cfg["access_token"]),
        },
    }

    if platform not in mappings:
        raise ValueError(f"Unsupported platform type: {platform}")

    required_fields = mappings[platform]["required"]
    missing = [field for field in required_fields if not config.get(field)]
    if missing:
        raise ValueError(f"Missing required field(s) for {platform}: {', '.join(missing)}")

    return mappings[platform]["factory"](config)
