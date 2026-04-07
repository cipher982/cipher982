#!/usr/bin/env python3
"""Validate external links in markdown and HTML fragments."""

from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\((https?://[^)\s]+)\)")
HTML_ATTR_RE = re.compile(r"""(?:href|src)=["'](https?://[^"' ]+)["']""")

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/135.0.0.0 Safari/537.36"
)


def extract_urls(path: Path) -> list[str]:
    text = path.read_text()
    seen: set[str] = set()
    urls: list[str] = []

    for regex in (MARKDOWN_LINK_RE, HTML_ATTR_RE):
        for url in regex.findall(text):
            if url not in seen:
                seen.add(url)
                urls.append(url)

    return urls


def check_url(url: str, timeout: int) -> tuple[bool, int | None, str, str | None]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", response.getcode())
            final_url = response.geturl()
            return 200 <= status < 400, status, final_url, None
    except urllib.error.HTTPError as exc:
        return False, exc.code, exc.geturl(), str(exc)
    except Exception as exc:  # noqa: BLE001
        return False, None, url, str(exc)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Markdown or HTML files to validate")
    parser.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="Per-request timeout in seconds (default: 20)",
    )
    args = parser.parse_args()

    failures = 0

    for raw_path in args.paths:
        path = Path(raw_path)
        urls = extract_urls(path)
        print(f"\n# {path} ({len(urls)} links)")

        for url in urls:
            ok, status, final_url, error = check_url(url, timeout=args.timeout)
            status_label = status if status is not None else "ERR"

            if ok:
                extra = f" -> {final_url}" if final_url != url else ""
                print(f"OK   {status_label} {url}{extra}")
                continue

            failures += 1
            detail = error or ""
            extra = f" -> {final_url}" if final_url != url else ""
            print(f"FAIL {status_label} {url}{extra} {detail}".rstrip())

    if failures:
        print(f"\nFound {failures} broken link(s).", file=sys.stderr)
        return 1

    print("\nAll checked links passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
