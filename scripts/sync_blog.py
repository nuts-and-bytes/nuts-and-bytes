#!/usr/bin/env python3
"""Sync the latest 3 posts from https://blog.heystone.site/rss.xml into README.md."""

from email.utils import parsedate_to_datetime
import pathlib
import re
import urllib.request
import xml.etree.ElementTree as ET

RSS_URL = "https://blog.heystone.site/rss.xml"
README = pathlib.Path(__file__).resolve().parent.parent / "README.md"
START = "<!-- BLOG-POST-LIST:START -->"
END = "<!-- BLOG-POST-LIST:END -->"
MAX_ITEMS = 3


def fetch_latest_posts(limit: int = MAX_ITEMS) -> list[tuple[str, str, str]]:
    req = urllib.request.Request(RSS_URL, headers={"User-Agent": "nuts-and-bytes-profile-sync/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        xml_bytes = resp.read()
    root = ET.fromstring(xml_bytes)
    posts: list[tuple[str, str, str]] = []
    for item in root.findall(".//item")[:limit]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_raw = (item.findtext("pubDate") or "").strip()
        date_str = ""
        if pub_raw:
            try:
                date_str = parsedate_to_datetime(pub_raw).strftime("%Y-%m-%d")
            except Exception:
                date_str = pub_raw[:10]
        if title and link:
            posts.append((date_str, title, link))
    return posts


def render_markdown(posts: list[tuple[str, str, str]]) -> str:
    lines = []
    for date_str, title, link in posts:
        prefix = f"`{date_str}` · " if date_str else ""
        lines.append(f"- {prefix}[{title} ↗]({link})")
    return "\n".join(lines)


def main() -> None:
    posts = fetch_latest_posts()
    if not posts:
        raise SystemExit("No posts found in RSS feed; skipping update.")
    content = README.read_text(encoding="utf-8")
    pattern = re.compile(rf"{re.escape(START)}.*?{re.escape(END)}", re.S)
    replacement = f"{START}\n{render_markdown(posts)}\n{END}"
    updated, count = pattern.subn(replacement, content, count=1)
    if count != 1:
        raise SystemExit("BLOG-POST-LIST markers not found in README.md")
    if updated != content:
        README.write_text(updated, encoding="utf-8")
        print(f"Updated README.md with {len(posts)} latest blog posts.")
    else:
        print("README.md is already up to date.")


if __name__ == "__main__":
    main()
