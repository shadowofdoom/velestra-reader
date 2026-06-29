"""Command line interface for velestra-reader."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .client import VelestraReaderClient
from .config import load_config
from .formatter import format_thread


def _write_output(content: str, output_path: str | None) -> None:
    if output_path:
        Path(output_path).write_text(content, encoding="utf-8")
    else:
        sys.stdout.write(content)


def _json_text(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="velestra-reader",
        description="Read public Reddit content through the approved OAuth Data API flow.",
    )
    parser.add_argument("--config", help="Path to a VELESTRA_READER_* config.env file")
    subparsers = parser.add_subparsers(dest="command", required=True)

    thread = subparsers.add_parser("thread", help="Fetch and format a public Reddit thread")
    thread.add_argument("url", help="Reddit thread URL")
    thread.add_argument("--json", action="store_true", help="Print raw JSON instead of text")
    thread.add_argument("--output", help="Write output to a file")

    subreddit = subparsers.add_parser("subreddit", help="Fetch a public subreddit listing")
    subreddit.add_argument("name", help="Subreddit name, with or without r/ prefix")
    subreddit.add_argument("--sort", default="hot", choices=["hot", "new", "top", "rising", "controversial"])
    subreddit.add_argument("--time", default="all", choices=["hour", "day", "week", "month", "year", "all"])
    subreddit.add_argument("--limit", type=int, default=25)
    subreddit.add_argument("--output", help="Write JSON output to a file")

    search = subparsers.add_parser("search", help="Fetch public Reddit search results")
    search.add_argument("query", help="Search query")
    search.add_argument("--subreddit", help="Limit search to a subreddit")
    search.add_argument("--sort", default="relevance", choices=["relevance", "hot", "top", "new", "comments"])
    search.add_argument("--time", default="all", choices=["hour", "day", "week", "month", "year", "all"])
    search.add_argument("--limit", type=int, default=25)
    search.add_argument("--output", help="Write JSON output to a file")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(config_path=Path(args.config) if args.config else None)
    client = VelestraReaderClient(config)

    if args.command == "thread":
        payload = client.fetch_thread(args.url)
        content = _json_text(payload) if args.json else format_thread(payload)
        _write_output(content, args.output)
        return 0

    if args.command == "subreddit":
        payload = client.fetch_subreddit(args.name, sort=args.sort, time=args.time, limit=args.limit)
        _write_output(_json_text(payload), args.output)
        return 0

    if args.command == "search":
        payload = client.search(
            args.query,
            subreddit=args.subreddit,
            sort=args.sort,
            time=args.time,
            limit=args.limit,
        )
        _write_output(_json_text(payload), args.output)
        return 0

    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
