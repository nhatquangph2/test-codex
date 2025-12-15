import logging
from unittest.mock import Mock

import pytest

from social_agent.platform_clients import (
    FacebookClient,
    InstagramClient,
    SocialClientError,
    TikTokClient,
    YouTubeClient,
    create_client,
)


def _response(status_code=200, json_data=None, text=""):
    response = Mock()
    response.status_code = status_code
    response.ok = status_code < 400
    response.text = text
    response.json = Mock(return_value=json_data or {})
    return response


def test_create_client_requires_type():
    with pytest.raises(ValueError):
        create_client({})


def test_create_client_missing_required_field():
    with pytest.raises(ValueError):
        create_client({"type": "facebook", "access_token": "token"})


def test_facebook_payload(monkeypatch):
    response = _response(json_data={"id": "123"})
    client = FacebookClient(page_id="42", access_token="token")

    captured = {}

    def fake_post(url, json_payload=None, headers=None):
        captured.update({"url": url, "json": json_payload, "headers": headers})
        return response

    monkeypatch.setattr(client, "session", Mock(post=fake_post))

    result = client.publish({"message": "hello", "link": "https://example.com"})

    assert result == {"id": "123"}
    assert captured["url"].endswith("/42/feed")
    assert captured["json"]["message"] == "hello"
    assert captured["json"]["link"] == "https://example.com"
    assert captured["json"]["access_token"] == "token"
    assert captured["headers"] == {}


def test_instagram_payload(monkeypatch):
    responses = [_response(json_data={"id": "ig_container"}), _response(json_data={"id": "ig_post"})]
    client = InstagramClient(business_account_id="ig-business", access_token="insta-token")

    captured = []

    def fake_post(url, json_payload=None, headers=None):
        captured.append({"url": url, "json": json_payload, "headers": headers})
        return responses.pop(0)

    monkeypatch.setattr(client, "session", Mock(post=fake_post))

    result = client.publish({"image_url": "https://example.com/photo.jpg", "caption": "Caption"})

    assert result == {"id": "ig_post"}
    assert captured[0]["url"].endswith("/ig-business/media")
    assert captured[0]["json"] == {
        "image_url": "https://example.com/photo.jpg",
        "caption": "Caption",
        "access_token": "insta-token",
    }
    assert captured[0]["headers"] == {}
    assert captured[1]["url"].endswith("/ig-business/media_publish")
    assert captured[1]["json"] == {
        "creation_id": "ig_container",
        "access_token": "insta-token",
    }
    assert captured[1]["headers"] == {}


def test_error_logging_on_token_expiry(monkeypatch, caplog):
    response = _response(status_code=401, text="Token expired")
    client = TikTokClient(advertiser_id="1234", access_token="expired-token")
    monkeypatch.setattr(client, "session", Mock(post=lambda *args, **kwargs: response))

    with caplog.at_level(logging.ERROR):
        with pytest.raises(SocialClientError):
            client.publish({"caption": "fail", "video_url": "https://example.com/video.mp4"})

    assert "token expired" in caplog.text.lower()



def test_youtube_payload_and_error(monkeypatch, caplog):
    response = _response(status_code=500, text="Backend error")
    client = YouTubeClient(channel_id="UC123", access_token="yt-token")

    captured = {}

    def fake_post(url, json_payload=None, headers=None):
        captured.update({"url": url, "json": json_payload, "headers": headers})
        return response

    monkeypatch.setattr(client, "session", Mock(post=fake_post))

    with caplog.at_level(logging.ERROR):
        with pytest.raises(SocialClientError):
            client.publish(
                {
                    "title": "Demo",
                    "description": "desc",
                    "privacy_status": "public",
                    "video_data": b"video-bytes",
                }
            )

    assert captured["headers"]["Authorization"] == "Bearer yt-token"
    assert captured["headers"]["X-Upload-Content-ChannelId"] == "UC123"
    assert captured["url"].endswith("uploadType=multipart")
    assert captured["json"]["media_body"] == b"video-bytes"
    assert "api error" in caplog.text.lower()
