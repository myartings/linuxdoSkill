#!/usr/bin/env python3
"""Search public linux.do links via Brave Search HTML.

This avoids hitting linux.do JSON endpoints directly, which are often blocked
by Cloudflare challenges for non-browser clients.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
import urllib.parse
import urllib.error
import urllib.request

from parse_linuxdo_url import parse_linuxdo_url


BRAVE_SEARCH = "https://search.brave.com/search"
BING_RSS = "https://www.bing.com/search"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
)


def fetch_brave_html(query: str) -> str:
    params = urllib.parse.urlencode({"q": query, "source": "web"})
    req = urllib.request.Request(
        f"{BRAVE_SEARCH}?{params}",
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", "ignore")


def fetch_bing_rss(query: str) -> str:
    params = urllib.parse.urlencode({"q": query, "format": "rss"})
    req = urllib.request.Request(
        f"{BING_RSS}?{params}",
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", "ignore")


def normalize_url(url: str) -> str:
    url = urllib.parse.unquote(url)
    url = url.replace("\\u002F", "/")
    return url.rstrip('",')


def result_priority(url: str) -> tuple[int, str]:
    if "/t/" in url:
        return (0, url)
    if "/c/" in url:
        return (1, url)
    if "/tag/" in url:
        return (2, url)
    if "/u/" in url:
        return (3, url)
    return (9, url)


def extract_results(page_html: str) -> list[str]:
    candidates = re.findall(r"https://linux\.do/[^\"'<>\s\\]+", page_html)
    seen: set[str] = set()
    cleaned: list[str] = []

    ignored = {
        "https://linux.do/",
        "https://linux.do/latest?tl=en",
        "https://linux.do/guidelines?tl=en",
    }

    for raw in candidates:
        url = normalize_url(raw)
        if url in ignored:
            continue
        if url in seen:
            continue
        seen.add(url)
        cleaned.append(url)

    cleaned.sort(key=result_priority)
    return cleaned


def extract_bing_rss_results(xml_text: str) -> list[str]:
    root = ET.fromstring(xml_text)
    urls: list[str] = []
    seen: set[str] = set()
    ignored = {
        "https://linux.do/",
        "https://linux.do/latest?tl=en",
        "https://linux.do/guidelines?tl=en",
    }
    for item in root.findall("./channel/item"):
        link = item.findtext("link")
        if not link or "linux.do/" not in link:
            continue
        link = normalize_url(link)
        if link in ignored or link in seen:
            continue
        seen.add(link)
        urls.append(link)
    urls.sort(key=result_priority)
    return urls


def search_links(query: str) -> list[str]:
    failures: list[str] = []

    try:
        return extract_results(fetch_brave_html(query))
    except urllib.error.HTTPError as exc:
        failures.append(f"brave_http_{exc.code}")
    except Exception as exc:
        failures.append(f"brave_{type(exc).__name__}")

    try:
        return extract_bing_rss_results(fetch_bing_rss(query))
    except urllib.error.HTTPError as exc:
        failures.append(f"bing_http_{exc.code}")
    except Exception as exc:
        failures.append(f"bing_{type(exc).__name__}")

    raise RuntimeError("search backends failed: " + ", ".join(failures))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Search public linux.do links via Brave Search HTML."
    )
    parser.add_argument("keywords", nargs="+", help="Search keywords")
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of results to print (default: 5)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print structured JSON instead of plain text.",
    )
    args = parser.parse_args()

    query = " ".join(args.keywords).strip()
    if "site:linux.do" not in query:
        query = f"site:linux.do {query}"

    try:
        results = search_links(query)
    except Exception as exc:  # pragma: no cover
        print(f"Search failed: {exc}", file=sys.stderr)
        return 1

    if not results:
        print("No linux.do results found.")
        return 2

    if args.json:
        payload = [
            {
                "rank": idx,
                "url": url,
                "parsed": parse_linuxdo_url(url),
            }
            for idx, url in enumerate(results[: args.limit], start=1)
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    for idx, url in enumerate(results[: args.limit], start=1):
        print(f"{idx}. {url}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
