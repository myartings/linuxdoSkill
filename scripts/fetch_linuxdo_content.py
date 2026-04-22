#!/usr/bin/env python3
"""Fetch linux.do topic content via headless Chromium (bypasses Cloudflare).

Strategy: navigate to the page first to establish a CF-verified browser session,
then call the Discourse JSON API from within that session using page.evaluate().

Requires: pip install playwright playwright-stealth
Browser:  system chromium at /usr/bin/chromium (or set CHROMIUM_PATH env var)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from extract_linuxdo_structured import clean_text  # noqa: E402
from parse_linuxdo_url import parse_linuxdo_url    # noqa: E402

CHROMIUM_PATH = os.environ.get("CHROMIUM_PATH", "/usr/bin/chromium")
CF_TITLES = {"just a moment", "请稍候", "checking your browser"}


def _is_cf_title(title: str) -> bool:
    return any(t in title.lower() for t in CF_TITLES)


def _in_browser_fetch(page, path: str) -> dict:
    """Run fetch() inside the browser session and return parsed JSON."""
    return page.evaluate(f"""
        async () => {{
            const r = await fetch({json.dumps(path)},
                {{headers: {{Accept: 'application/json'}}}});
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        }}
    """)


def _get_category_name(page, category_id: int | None) -> str | None:
    """Read category name from Discourse's PreloadStore (already in page)."""
    if category_id is None:
        return None
    return page.evaluate(f"""
        () => {{
            try {{
                const site = window.PreloadStore && window.PreloadStore.get('site');
                const cats = (site && site.categories) || [];
                const cat = cats.find(c => c.id === {category_id});
                return cat ? cat.name : null;
            }} catch(e) {{ return null; }}
        }}
    """)


def fetch_topic(url: str, post_number: int | None = None, timeout_ms: int = 30_000) -> dict:
    """Return structured topic data. Raises RuntimeError on hard failures."""
    try:
        from playwright.sync_api import sync_playwright
        from playwright_stealth import Stealth
    except ImportError as exc:
        raise RuntimeError(
            f"Missing dependency: {exc}. "
            "Run: pip install playwright playwright-stealth"
        ) from exc

    parsed = parse_linuxdo_url(url)
    topic_id = parsed.get("topic_id")
    if not topic_id:
        raise RuntimeError(f"Cannot extract topic_id from URL: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROMIUM_PATH,
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        ctx = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            locale="zh-CN",
        )
        page = ctx.new_page()
        Stealth().apply_stealth_sync(page)

        # Navigate to establish CF-verified session
        page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
        if _is_cf_title(page.title()):
            page.wait_for_function(
                "() => !document.title.toLowerCase().includes('moment')"
                " && !document.title.includes('请稍候')",
                timeout=timeout_ms,
            )

        # Fetch topic metadata via Discourse JSON API (same browser session)
        topic_data = _in_browser_fetch(page, f"/t/{topic_id}.json")

        title = topic_data.get("title")
        category_id = topic_data.get("category_id")
        category_name = _get_category_name(page, category_id)
        stream: list[int] = topic_data.get("post_stream", {}).get("stream", [])
        initial_posts: list[dict] = topic_data.get("post_stream", {}).get("posts", [])

        # Resolve which posts to return
        if post_number is not None:
            target = [p for p in initial_posts if p.get("post_number") == post_number]
            if not target and post_number <= len(stream):
                post_id = stream[post_number - 1]
                extra = _in_browser_fetch(
                    page, f"/t/{topic_id}/posts.json?post_ids[]={post_id}"
                )
                target = extra.get("post_stream", {}).get("posts", [])
        else:
            target = initial_posts

        browser.close()

    posts_out = [
        {
            "post_number": p.get("post_number"),
            "post_id": p.get("id"),
            "username": p.get("username"),
            "created_at": p.get("created_at"),
            "content": clean_text(p.get("cooked") or ""),
        }
        for p in target
    ]

    return {
        "status": "ok",
        "source": url,
        "topic_id": topic_id,
        "title": title,
        "category": category_name,
        "post_count": len(posts_out),
        "posts": posts_out,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch linux.do topic content via headless Chromium."
    )
    parser.add_argument("url", help="linux.do topic URL")
    parser.add_argument("--post-number", type=int, help="Return only this post number")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout in seconds (default: 30)")
    args = parser.parse_args()

    try:
        data = fetch_topic(args.url, post_number=args.post_number, timeout_ms=args.timeout * 1000)
    except Exception as exc:
        result = {"status": "error", "error": str(exc), "url": args.url}
        print(json.dumps(result, ensure_ascii=False))
        return 1

    indent = 2 if args.pretty else None
    print(json.dumps(data, ensure_ascii=False, indent=indent, sort_keys=True))
    return 0 if data.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
