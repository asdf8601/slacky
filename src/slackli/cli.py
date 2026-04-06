from __future__ import annotations

import os
import sys

import click

from slackli.client import SlackClient, SlackError
from slackli.formatters import (
    print_channels,
    print_error,
    print_messages,
    print_search_results,
    print_success,
    print_users,
)


def _get_client() -> SlackClient:
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        print_error(
            "SLACK_BOT_TOKEN not set. "
            "Export your bot token: export SLACK_BOT_TOKEN=xoxb-..."
        )
        sys.exit(1)
    return SlackClient(token)


@click.group()
@click.version_option(package_name="slackli")
def main() -> None:
    """slackli — Slack from your terminal."""


# --- Send ---


@main.command()
@click.argument("target")
@click.argument("text")
@click.option(
    "--thread",
    "-t",
    default=None,
    help="Thread timestamp to reply to.",
)
def send(target: str, text: str, thread: str | None) -> None:
    """Send a message to a channel or user.

    TARGET can be #channel-name, a channel ID, or @username.
    """
    client = _get_client()
    try:
        if target.startswith("@"):
            users = client.find_user(target.lstrip("@"))
            if not users:
                print_error(f"User not found: {target}")
                return
            msg = client.send_dm(users[0].id, text)
            print_success(f"DM sent to {users[0].real_name} (ts: {msg.ts})")
        else:
            channel_id = client.resolve_channel(target)
            msg = client.send_message(channel_id, text, thread_ts=thread)
            print_success(f"Message sent to {target} (ts: {msg.ts})")
    except SlackError as e:
        print_error(str(e))


# --- Read ---


@main.command()
@click.argument("target")
@click.option(
    "--limit",
    "-n",
    default=20,
    help="Number of messages to fetch.",
)
def read(target: str, limit: int) -> None:
    """Read messages from a channel or DM.

    TARGET can be #channel-name, a channel ID, or @username.
    """
    client = _get_client()
    try:
        if target.startswith("@"):
            users = client.find_user(target.lstrip("@"))
            if not users:
                print_error(f"User not found: {target}")
                return
            messages = client.read_dm(users[0].id, limit=limit)
            title = f"DM with {users[0].real_name}"
        else:
            channel_id = client.resolve_channel(target)
            messages = client.read_messages(channel_id, limit=limit)
            title = f"Messages in {target}"
        print_messages(messages, title=title)
    except SlackError as e:
        print_error(str(e))


# --- Thread ---


@main.command()
@click.argument("channel")
@click.argument("thread_ts")
@click.option(
    "--limit",
    "-n",
    default=50,
    help="Number of replies to fetch.",
)
def thread(channel: str, thread_ts: str, limit: int) -> None:
    """Read a thread's replies.

    CHANNEL can be #channel-name or a channel ID.
    THREAD_TS is the timestamp of the parent message.
    """
    client = _get_client()
    try:
        channel_id = client.resolve_channel(channel)
        messages = client.read_thread(channel_id, thread_ts, limit=limit)
        print_messages(messages, title=f"Thread {thread_ts}")
    except SlackError as e:
        print_error(str(e))


# --- Channels ---


@main.command()
@click.argument("query", required=False)
@click.option(
    "--limit",
    "-n",
    default=100,
    help="Max channels to fetch.",
)
def channels(query: str | None, limit: int) -> None:
    """List or search channels.

    Optionally filter by QUERY (matches name, topic, purpose).
    """
    client = _get_client()
    try:
        results = client.list_channels(query=query, limit=limit)
        if not results:
            print_error(f"No channels found matching: {query}")
            return
        print_channels(results)
    except SlackError as e:
        print_error(str(e))


# --- Search ---


@main.command()
@click.argument("query")
@click.option(
    "--sort",
    "-s",
    type=click.Choice(["timestamp", "score"]),
    default="timestamp",
    help="Sort order.",
)
@click.option(
    "--limit",
    "-n",
    default=20,
    help="Number of results.",
)
def search(query: str, sort: str, limit: int) -> None:
    """Search messages across channels.

    Supports Slack search syntax:
      in:#channel, from:@user, before:2024-01-01, after:2024-01-01
    """
    client = _get_client()
    try:
        results = client.search_messages(query, sort=sort, count=limit)
        if not results:
            print_error(f"No results for: {query}")
            return
        print_search_results(results)
    except SlackError as e:
        print_error(str(e))


# --- Users ---


@main.command()
@click.argument("name")
def users(name: str) -> None:
    """Find users by name or username."""
    client = _get_client()
    try:
        results = client.find_user(name)
        if not results:
            print_error(f"No users found matching: {name}")
            return
        print_users(results)
    except SlackError as e:
        print_error(str(e))
