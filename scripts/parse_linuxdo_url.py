#!/usr/bin/env python3
"""Parse linux.do URLs into structured metadata."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse


def parse_linuxdo_url(url: str) -> dict[str, object]:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.netloc != "linux.do":
        raise ValueError("URL must be an absolute https://linux.do/... link")

    path = parsed.path.rstrip("/")
    query = urllib.parse.parse_qs(parsed.query)

    result: dict[str, object] = {
        "url": url,
        "scheme": parsed.scheme,
        "host": parsed.netloc,
        "path": parsed.path,
        "query": {k: v[0] if len(v) == 1 else v for k, v in query.items()},
        "resource_type": "unknown",
    }

    m = re.match(r"^/t/[^/]+/(\d+)(?:/(\d+))?$", path)
    if m:
        result["resource_type"] = "topic_post"
        result["topic_id"] = int(m.group(1))
        if m.group(2):
            result["post_number"] = int(m.group(2))
        if "page" in query:
            try:
                result["page"] = int(query["page"][0])
            except ValueError:
                result["page"] = query["page"][0]
        return result

    m = re.match(r"^/t/topic/(\d+)(?:/(\d+))?$", path)
    if m:
        result["resource_type"] = "topic_post"
        result["topic_id"] = int(m.group(1))
        if m.group(2):
            result["post_number"] = int(m.group(2))
        if "page" in query:
            try:
                result["page"] = int(query["page"][0])
            except ValueError:
                result["page"] = query["page"][0]
        return result

    m = re.match(r"^/c/([^/]+)(?:/(\d+))?$", path)
    if m:
        result["resource_type"] = "category"
        result["category_slug"] = m.group(1)
        if m.group(2):
            result["category_id"] = int(m.group(2))
        return result

    m = re.match(r"^/tag/([^/]+)$", path)
    if m:
        result["resource_type"] = "tag"
        result["tag"] = m.group(1)
        return result

    m = re.match(r"^/u/([^/]+)$", path)
    if m:
        result["resource_type"] = "user"
        result["username"] = m.group(1)
        return result

    if path in {"", "/"}:
        result["resource_type"] = "home"
        return result

    if path == "/latest":
        result["resource_type"] = "latest"
        return result

    if path == "/guidelines":
        result["resource_type"] = "guidelines"
        return result

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse a linux.do URL to JSON.")
    parser.add_argument("url", help="Absolute linux.do URL")
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output",
    )
    args = parser.parse_args()

    try:
        data = parse_linuxdo_url(args.url)
    except Exception as exc:
        print(f"Parse failed: {exc}", file=sys.stderr)
        return 1

    if args.pretty:
        print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(json.dumps(data, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
