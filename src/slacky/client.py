from __future__ import annotations

import re
import time
from dataclasses import dataclass

import httpx

BASE_URL = "https://slack.com/api"

_SLACK_URL_RE = re.compile(
    r"https?://[^/]+\.slack\.com/archives/([A-Z0-9]+)/p(\d+)"
)


def parse_slack_url(url: str) -> tuple[str, str] | None:
    """Parse a Slack message URL into (channel_id, thread_ts).

    URL format: https://<workspace>.slack.com/archives/<channel>/p<ts>
    The timestamp has no dot — insert '.' before the last 6 digits.
    """
    m = _SLACK_URL_RE.match(url)
    if not m:
        return None
    channel_id = m.group(1)
    raw_ts = m.group(2)
    ts = f"{raw_ts[:-6]}.{raw_ts[-6:]}"
    return channel_id, ts


@dataclass
class Message:
    ts: str
    user: str
    text: str
    thread_ts: str | None = None
    reply_count: int = 0


@dataclass
class Channel:
    id: str
    name: str
    topic: str
    purpose: str
    is_member: bool
    num_members: int


@dataclass
class User:
    id: str
    name: str
    real_name: str
    display_name: str


@dataclass
class SearchResult:
    channel: str
    user: str
    text: str
    ts: str
    permalink: str


class SlackError(Exception):
    def __init__(self, method: str, error: str) -> None:
        self.method = method
        self.error = error
        super().__init__(f"Slack API error on {method}: {error}")


class SlackClient:
    def __init__(self, token: str) -> None:
        self._http = httpx.Client(
            base_url=BASE_URL,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )

    def _call(
        self,
        method: str,
        *,
        post: bool = False,
        json: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        for _ in range(5):
            if post:
                resp = self._http.post(f"/{method}", json=json)
            else:
                resp = self._http.get(f"/{method}", params=params)
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 3))
                time.sleep(retry_after)
                continue
            resp.raise_for_status()
            data = resp.json()
            if not data.get("ok"):
                raise SlackError(method, data.get("error", "unknown"))
            return data
        resp.raise_for_status()
        return {}  # unreachable

    # --- Messages ---

    def send_message(
        self,
        channel: str,
        text: str,
        thread_ts: str | None = None,
    ) -> Message:
        payload: dict = {"channel": channel, "text": text}
        if thread_ts:
            payload["thread_ts"] = thread_ts
        data = self._call("chat.postMessage", post=True, json=payload)
        msg = data["message"]
        return Message(
            ts=msg["ts"],
            user=msg.get("user", "bot"),
            text=msg.get("text", ""),
        )

    def read_messages(
        self,
        channel: str,
        limit: int = 20,
    ) -> list[Message]:
        data = self._call(
            "conversations.history",
            params={"channel": channel, "limit": limit},
        )
        return [
            Message(
                ts=m["ts"],
                user=m.get("user", "unknown"),
                text=m.get("text", ""),
                thread_ts=m.get("thread_ts"),
                reply_count=m.get("reply_count", 0),
            )
            for m in data.get("messages", [])
        ]

    # --- Threads ---

    def read_thread(
        self,
        channel: str,
        thread_ts: str,
        limit: int = 50,
    ) -> list[Message]:
        data = self._call(
            "conversations.replies",
            params={
                "channel": channel,
                "ts": thread_ts,
                "limit": limit,
            },
        )
        return [
            Message(
                ts=m["ts"],
                user=m.get("user", "unknown"),
                text=m.get("text", ""),
                thread_ts=m.get("thread_ts"),
            )
            for m in data.get("messages", [])
        ]

    # --- DMs ---

    def open_dm(self, user_id: str) -> str:
        data = self._call(
            "conversations.open",
            post=True,
            json={"users": user_id},
        )
        return data["channel"]["id"]

    def send_dm(self, user_id: str, text: str) -> Message:
        channel_id = self.open_dm(user_id)
        return self.send_message(channel_id, text)

    def read_dm(self, user_id: str, limit: int = 20) -> list[Message]:
        channel_id = self.open_dm(user_id)
        return self.read_messages(channel_id, limit)

    # --- Channels ---

    def list_channels(
        self,
        query: str | None = None,
        limit: int = 1000,
    ) -> list[Channel]:
        channels: list[Channel] = []
        cursor: str | None = None
        while True:
            params: dict = {
                "limit": min(limit, 1000),
                "types": "public_channel,private_channel",
                "exclude_archived": "true",
            }
            if cursor:
                params["cursor"] = cursor
            data = self._call("conversations.list", params=params)
            for c in data.get("channels", []):
                channels.append(
                    Channel(
                        id=c["id"],
                        name=c.get("name", ""),
                        topic=c.get("topic", {}).get("value", ""),
                        purpose=c.get("purpose", {}).get("value", ""),
                        is_member=c.get("is_member", False),
                        num_members=c.get("num_members", 0),
                    )
                )
            cursor = data.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
        if query:
            q = query.lower()
            channels = [
                c
                for c in channels
                if q in c.name.lower()
                or q in c.topic.lower()
                or q in c.purpose.lower()
            ]
        return channels

    # --- Search ---

    def search_messages(
        self,
        query: str,
        sort: str = "timestamp",
        count: int = 20,
    ) -> list[SearchResult]:
        data = self._call(
            "search.messages",
            params={
                "query": query,
                "sort": sort,
                "count": count,
            },
        )
        matches = data.get("messages", {}).get("matches", [])
        return [
            SearchResult(
                channel=m.get("channel", {}).get("name", "unknown"),
                user=m.get("username", "unknown"),
                text=m.get("text", ""),
                ts=m.get("ts", ""),
                permalink=m.get("permalink", ""),
            )
            for m in matches
        ]

    # --- Users ---

    def find_user(self, name: str) -> list[User]:
        data = self._call("users.list", params={"limit": 500})
        users = []
        q = name.lower()
        for u in data.get("members", []):
            if u.get("deleted") or u.get("is_bot"):
                continue
            profile = u.get("profile", {})
            real_name = profile.get("real_name", "")
            display_name = profile.get("display_name", "")
            uname = u.get("name", "")
            if (
                q in uname.lower()
                or q in real_name.lower()
                or q in display_name.lower()
            ):
                users.append(
                    User(
                        id=u["id"],
                        name=uname,
                        real_name=real_name,
                        display_name=display_name,
                    )
                )
        return users

    def resolve_channel(self, name_or_id: str) -> str:
        if name_or_id.startswith("C") or name_or_id.startswith("D"):
            return name_or_id
        clean = name_or_id.lstrip("#")
        channels = self.list_channels(query=clean)
        exact = [c for c in channels if c.name == clean]
        if exact:
            return exact[0].id
        if channels:
            return channels[0].id
        raise SlackError("resolve_channel", f"channel not found: {name_or_id}")
