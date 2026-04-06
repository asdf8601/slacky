from __future__ import annotations

from datetime import UTC, datetime

from rich.console import Console
from rich.table import Table
from rich.text import Text

from slacky.client import Channel, Message, SearchResult, User

console = Console()


def _format_ts(ts: str) -> str:
    try:
        dt = datetime.fromtimestamp(float(ts), tz=UTC)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OSError):
        return ts


def print_messages(messages: list[Message], title: str = "Messages") -> None:
    table = Table(title=title, show_lines=True)
    table.add_column("Time", style="dim", width=20)
    table.add_column("User", style="cyan", width=15)
    table.add_column("Message", style="white")
    table.add_column("Thread", style="yellow", width=8)

    for msg in reversed(messages):
        thread_info = ""
        if msg.reply_count > 0:
            thread_info = f"💬 {msg.reply_count}"
        elif msg.thread_ts and msg.thread_ts != msg.ts:
            thread_info = "↩"

        table.add_row(
            _format_ts(msg.ts),
            msg.user,
            Text(msg.text, overflow="fold"),
            thread_info,
        )

    console.print(table)


def print_channels(channels: list[Channel]) -> None:
    table = Table(title="Channels", show_lines=False)
    table.add_column("Name", style="cyan")
    table.add_column("ID", style="dim")
    table.add_column("Members", justify="right")
    table.add_column("Member?", justify="center")
    table.add_column("Topic", style="white", max_width=50)

    for ch in channels:
        table.add_row(
            f"#{ch.name}",
            ch.id,
            str(ch.num_members),
            "✓" if ch.is_member else "",
            Text(ch.topic or ch.purpose, overflow="ellipsis"),
        )

    console.print(table)


def print_users(users: list[User]) -> None:
    table = Table(title="Users", show_lines=False)
    table.add_column("Username", style="cyan")
    table.add_column("ID", style="dim")
    table.add_column("Real Name", style="white")
    table.add_column("Display Name", style="yellow")

    for u in users:
        table.add_row(u.name, u.id, u.real_name, u.display_name)

    console.print(table)


def print_search_results(results: list[SearchResult]) -> None:
    table = Table(title="Search Results", show_lines=True)
    table.add_column("Time", style="dim", width=20)
    table.add_column("Channel", style="cyan", width=15)
    table.add_column("User", style="yellow", width=15)
    table.add_column("Message", style="white")

    for r in results:
        table.add_row(
            _format_ts(r.ts),
            f"#{r.channel}",
            r.user,
            Text(r.text, overflow="fold"),
        )

    console.print(table)


def print_success(text: str) -> None:
    console.print(f"[green]✓[/green] {text}")


def print_error(text: str) -> None:
    console.print(f"[red]✗[/red] {text}")
