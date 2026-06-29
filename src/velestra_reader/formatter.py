"""Formatting helpers for local reading."""

from __future__ import annotations

from typing import Any


def _clean_text(value: Any) -> str:
    text = "" if value is None else str(value)
    return " ".join(text.split())


def _comment_lines(children: list[dict[str, Any]], *, depth: int = 0) -> list[str]:
    lines: list[str] = []
    indent = "  " * depth
    for child in children:
        kind = child.get("kind")
        data = child.get("data") or {}
        if kind == "more":
            count = data.get("count", len(data.get("children") or []))
            lines.append(f"{indent}- [more comments omitted: {count}]")
            continue
        if kind != "t1":
            continue

        author = data.get("author", "[deleted]")
        score = data.get("score", 0)
        body = _clean_text(data.get("body"))
        lines.append(f"{indent}- {author} (score: {score}): {body}")

        replies = data.get("replies")
        if isinstance(replies, dict):
            reply_children = replies.get("data", {}).get("children", [])
            if isinstance(reply_children, list):
                lines.extend(_comment_lines(reply_children, depth=depth + 1))
    return lines


def format_thread(payload: list[dict[str, Any]]) -> str:
    """Format a Reddit thread JSON response into compact local text."""
    if not isinstance(payload, list) or len(payload) < 2:
        raise ValueError("Expected Reddit thread JSON with post and comment listings.")

    post_children = payload[0].get("data", {}).get("children", [])
    if not post_children:
        raise ValueError("Thread JSON did not contain a post.")

    post = post_children[0].get("data", {})
    comment_children = payload[1].get("data", {}).get("children", [])

    lines = [
        f"Title: {_clean_text(post.get('title'))}",
        f"Author: {post.get('author', '[deleted]')}",
        f"Score: {post.get('score', 0)}",
        f"Comments: {post.get('num_comments', 0)}",
        f"Permalink: https://www.reddit.com{post.get('permalink', '')}",
        "",
    ]
    body = _clean_text(post.get("selftext"))
    if body:
        lines.extend(["Post:", body, ""])

    lines.append("Comment Tree:")
    lines.extend(_comment_lines(comment_children))
    return "\n".join(lines).rstrip() + "\n"
