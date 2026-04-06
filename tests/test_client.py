from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from slackli.client import (
    Message,
    SlackClient,
    SlackError,
    parse_slack_url,
)


@pytest.fixture
def client() -> SlackClient:
    return SlackClient("xoxb-fake-token")


def _mock_response(data: dict) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = {**data, "ok": True}
    resp.raise_for_status = MagicMock()
    return resp


class TestSendMessage:
    def test_send_message(self, client: SlackClient) -> None:
        with patch.object(client._http, "post") as mock_post:
            mock_post.return_value = _mock_response(
                {"message": {"ts": "123.456", "user": "U1", "text": "hi"}}
            )
            msg = client.send_message("C123", "hi")
            assert isinstance(msg, Message)
            assert msg.ts == "123.456"
            assert msg.text == "hi"

    def test_send_message_with_thread(self, client: SlackClient) -> None:
        with patch.object(client._http, "post") as mock_post:
            mock_post.return_value = _mock_response(
                {"message": {"ts": "123.789", "user": "U1", "text": "reply"}}
            )
            msg = client.send_message("C123", "reply", thread_ts="123.456")
            call_json = mock_post.call_args[1]["json"]
            assert call_json["thread_ts"] == "123.456"
            assert msg.text == "reply"


class TestReadMessages:
    def test_read_messages(self, client: SlackClient) -> None:
        with patch.object(client._http, "get") as mock_get:
            mock_get.return_value = _mock_response(
                {
                    "messages": [
                        {"ts": "1", "user": "U1", "text": "hello"},
                        {"ts": "2", "user": "U2", "text": "world"},
                    ]
                }
            )
            msgs = client.read_messages("C123", limit=10)
            assert len(msgs) == 2
            assert msgs[0].text == "hello"


class TestReadThread:
    def test_read_thread(self, client: SlackClient) -> None:
        with patch.object(client._http, "get") as mock_get:
            mock_get.return_value = _mock_response(
                {
                    "messages": [
                        {"ts": "1.0", "user": "U1", "text": "parent"},
                        {"ts": "1.1", "user": "U2", "text": "reply1"},
                    ]
                }
            )
            msgs = client.read_thread("C123", "1.0")
            assert len(msgs) == 2


class TestListChannels:
    def test_list_channels(self, client: SlackClient) -> None:
        with patch.object(client._http, "get") as mock_get:
            mock_get.return_value = _mock_response(
                {
                    "channels": [
                        {
                            "id": "C1",
                            "name": "general",
                            "topic": {"value": ""},
                            "purpose": {"value": ""},
                            "is_member": True,
                            "num_members": 50,
                        }
                    ]
                }
            )
            channels = client.list_channels()
            assert len(channels) == 1
            assert channels[0].name == "general"

    def test_list_channels_with_filter(self, client: SlackClient) -> None:
        with patch.object(client._http, "get") as mock_get:
            mock_get.return_value = _mock_response(
                {
                    "channels": [
                        {
                            "id": "C1",
                            "name": "general",
                            "topic": {"value": ""},
                            "purpose": {"value": ""},
                            "is_member": True,
                            "num_members": 50,
                        },
                        {
                            "id": "C2",
                            "name": "random",
                            "topic": {"value": ""},
                            "purpose": {"value": ""},
                            "is_member": False,
                            "num_members": 30,
                        },
                    ]
                }
            )
            channels = client.list_channels(query="general")
            assert len(channels) == 1
            assert channels[0].name == "general"


class TestFindUser:
    def test_find_user(self, client: SlackClient) -> None:
        with patch.object(client._http, "get") as mock_get:
            mock_get.return_value = _mock_response(
                {
                    "members": [
                        {
                            "id": "U1",
                            "name": "jdoe",
                            "deleted": False,
                            "is_bot": False,
                            "profile": {
                                "real_name": "John Doe",
                                "display_name": "johnd",
                            },
                        },
                        {
                            "id": "U2",
                            "name": "asmith",
                            "deleted": False,
                            "is_bot": False,
                            "profile": {
                                "real_name": "Alice Smith",
                                "display_name": "alice",
                            },
                        },
                    ]
                }
            )
            users = client.find_user("john")
            assert len(users) == 1
            assert users[0].name == "jdoe"


class TestParseSlackUrl:
    def test_parse_valid_url(self) -> None:
        result = parse_slack_url(
            "https://seedtag.slack.com/archives/C06KSHUFF61/p1773307094764839"
        )
        assert result == ("C06KSHUFF61", "1773307094.764839")

    def test_parse_invalid_url(self) -> None:
        assert parse_slack_url("not-a-url") is None
        assert parse_slack_url("https://google.com") is None

    def test_parse_channel_id(self) -> None:
        result = parse_slack_url(
            "https://team.slack.com/archives/C123ABC/p1234567890123456"
        )
        assert result is not None
        assert result[0] == "C123ABC"
        assert result[1] == "1234567890.123456"


class TestSlackError:
    def test_api_error(self, client: SlackClient) -> None:
        with patch.object(client._http, "get") as mock_get:
            resp = MagicMock()
            resp.json.return_value = {
                "ok": False,
                "error": "channel_not_found",
            }
            resp.raise_for_status = MagicMock()
            mock_get.return_value = resp
            with pytest.raises(SlackError, match="channel_not_found"):
                client.read_messages("C_INVALID")
