#!/usr/bin/env python3
"""Extract structured linux.do topic/post data from browser-fetched HTML."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path


def clean_text(text: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</p>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def extract_meta(html_text: str, pattern: str) -> str | None:
    match = re.search(pattern, html_text, flags=re.I | re.S)
    if not match:
        return None
    return html.unescape(match.group(1)).strip()


def extract_topic_title(html_text: str) -> str | None:
    for pattern in (
        r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"',
        r"<title>(.*?)</title>",
    ):
        value = extract_meta(html_text, pattern)
        if value:
            value = re.sub(r"\s*-\s*LINUX DO\s*$", "", value)
            return value.strip()
    return None


def extract_category(html_text: str) -> str | None:
    patterns = (
        r'<meta[^>]+property="article:section"[^>]+content="([^"]+)"',
        r'"categoryName"\s*:\s*"([^"]+)"',
        r'<span[^>]+class="category-name"[^>]*>(.*?)</span>',
    )
    for pattern in patterns:
        value = extract_meta(html_text, pattern)
        if value:
            return clean_text(value)
    return None


def extract_topic_id(html_text: str) -> int | None:
    for pattern in (
        r'data-topic-id="(\d+)"',
        r'"topic_id"\s*:\s*(\d+)',
        r'"topicId"\s*:\s*(\d+)',
    ):
        match = re.search(pattern, html_text)
        if match:
            return int(match.group(1))
    return None


def extract_posts(html_text: str) -> list[dict[str, object]]:
    posts: list[dict[str, object]] = []
    blocks = re.findall(
        r'(<article[^>]+data-post-number="[^"]+"[\s\S]*?</article>)',
        html_text,
        flags=re.I,
    )

    for block in blocks:
        number_match = re.search(r'data-post-number="(\d+)"', block)
        if not number_match:
            continue
        post_number = int(number_match.group(1))

        post_id_match = re.search(r'data-post-id="(\d+)"', block)
        username = None
        username_match = re.search(
            r'data-user-card="([^"]+)"|class="username[^"]*"[^>]*>@?([^<]+)<',
            block,
            flags=re.I,
        )
        if username_match:
            username = username_match.group(1) or username_match.group(2)
            username = username.strip()

        created_at = None
        created_match = re.search(
            r'<time[^>]+datetime="([^"]+)"',
            block,
            flags=re.I,
        )
        if created_match:
            created_at = created_match.group(1)

        cooked_match = re.search(
            r'<div[^>]+class="cooked[^"]*"[^>]*>([\s\S]*?)</div>',
            block,
            flags=re.I,
        )
        content = clean_text(cooked_match.group(1)) if cooked_match else None

        posts.append(
            {
                "post_number": post_number,
                "post_id": int(post_id_match.group(1)) if post_id_match else None,
                "username": username,
                "created_at": created_at,
                "content": content,
            }
        )

    return posts


def detect_challenge(html_text: str) -> bool:
    markers = (
        "Enable JavaScript and cookies to continue",
        "Just a moment...",
        "cf-challenge",
        "challenge-platform",
    )
    return any(marker in html_text for marker in markers)


def extract_structured(html_text: str, source: str | None = None) -> dict[str, object]:
    if detect_challenge(html_text):
        return {
            "status": "cloudflare_challenge",
            "source": source,
        }

    title = extract_topic_title(html_text)
    category = extract_category(html_text)
    topic_id = extract_topic_id(html_text)
    posts = extract_posts(html_text)

    return {
        "status": "ok",
        "source": source,
        "title": title,
        "category": category,
        "topic_id": topic_id,
        "post_count": len(posts),
        "posts": posts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract structured linux.do topic/post data from HTML."
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="HTML file path. If omitted, reads HTML from stdin.",
    )
    parser.add_argument(
        "--post-number",
        type=int,
        help="Return only one post number if present.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    args = parser.parse_args()

    if args.input:
        html_text = Path(args.input).read_text(encoding="utf-8")
        source = args.input
    else:
        html_text = sys.stdin.read()
        source = "stdin"

    data = extract_structured(html_text, source=source)
    if args.post_number is not None and data.get("status") == "ok":
        posts = data.get("posts", [])
        data["posts"] = [
            post for post in posts if post.get("post_number") == args.post_number
        ]
        data["post_count"] = len(data["posts"])

    if args.pretty:
        print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(json.dumps(data, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
