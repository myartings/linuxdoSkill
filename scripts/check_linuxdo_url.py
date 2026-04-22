#!/usr/bin/env python3
"""Check whether a linux.do URL is directly readable from this environment."""

from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
)


def check_url(url: str) -> tuple[str, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            status = getattr(resp, "status", 200)
            content_type = resp.headers.get("content-type", "")
            cf_mitigated = resp.headers.get("cf-mitigated", "")
            body = resp.read(1500).decode("utf-8", "ignore")

        if cf_mitigated:
            return (
                "cloudflare_challenge",
                f"status={status} cf_mitigated={cf_mitigated}",
            )
        if "Just a moment" in body or "Enable JavaScript and cookies to continue" in body:
            return ("cloudflare_challenge", f"status={status} challenge_page=true")
        return ("ok", f"status={status} content_type={content_type}")
    except urllib.error.HTTPError as exc:
        cf_mitigated = exc.headers.get("cf-mitigated", "")
        if cf_mitigated:
            return (
                "cloudflare_challenge",
                f"status={exc.code} cf_mitigated={cf_mitigated}",
            )
        return ("http_error", f"status={exc.code}")
    except Exception as exc:  # pragma: no cover
        return ("network_error", f"{type(exc).__name__}: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check whether a linux.do URL is directly readable."
    )
    parser.add_argument("url", help="linux.do URL to test")
    args = parser.parse_args()

    status, detail = check_url(args.url)
    print(status)
    print(detail)
    return 0 if status == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
