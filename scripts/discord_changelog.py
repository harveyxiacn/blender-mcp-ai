#!/usr/bin/env python3
"""Post the latest changelog section to a Discord webhook on release.

Runs in the Release GitHub Actions workflow (on a ``v*`` tag). Extracts the
section for the tag's version from both ``docs/en/CHANGELOG.md`` and
``docs/zh/CHANGELOG.md`` and posts a bilingual embed to the webhook in
``DISCORD_CHANGELOG_WEBHOOK``. Standard library only (no extra deps).

Local dry run (no webhook set -> prints what it would post):

    python scripts/discord_changelog.py v0.3.1
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

BLENDER_ORANGE = 0xEA7600
EMBED_LIMIT = 4000  # Discord embed description hard limit is 4096; leave headroom


def extract_section(text: str, version: str) -> str:
    """Return the changelog block for ``version`` (heading + body).

    Prefers an exact ``## [<version>]`` heading anywhere in the file. Falls back
    to ``## [Unreleased]`` ONLY when it is the topmost ``## [`` heading (its
    proper Keep-a-Changelog position) — a stale Unreleased section sitting below
    a released version is ignored. If neither matches, the language is skipped
    (returns "") rather than posting the wrong version's notes. Captures lines
    until the next ``## `` heading.
    """
    lines = text.splitlines()
    headings = [i for i, line in enumerate(lines) if line.strip().startswith("## [")]
    if not headings:
        return ""

    target = f"## [{version}]"
    start: int | None = next((i for i in headings if lines[i].strip().startswith(target)), None)
    if start is None and lines[headings[0]].strip().startswith("## [Unreleased]"):
        start = headings[0]
    if start is None:
        return ""

    body = [lines[start]]
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        body.append(line)
    return "\n".join(body).strip()


def read_changelog(path: Path, version: str) -> str:
    if not path.exists():
        return ""
    return extract_section(path.read_text(encoding="utf-8"), version)


def truncate(text: str, limit: int, link: str) -> str:
    if len(text) <= limit:
        return text
    suffix = f"\n\n… → {link}"
    return text[: max(0, limit - len(suffix))].rstrip() + suffix


def build_payload(tag: str, en: str, zh: str, release_url: str) -> dict[str, object]:
    embeds: list[dict[str, object]] = []
    if en:
        embeds.append(
            {
                "title": "📋 Changelog (English)",
                "description": truncate(en, EMBED_LIMIT, release_url),
                "color": BLENDER_ORANGE,
            }
        )
    if zh:
        embeds.append(
            {
                "title": "📋 更新日志（中文）",
                "description": truncate(zh, EMBED_LIMIT, release_url),
                "color": BLENDER_ORANGE,
            }
        )
    if not embeds:
        embeds.append(
            {"title": "📦 Release", "description": f"See {release_url}", "color": BLENDER_ORANGE}
        )
    return {
        "content": f"🎉 **Blender MCP AI {tag}** released — {release_url}",
        "embeds": embeds,
        "allowed_mentions": {"parse": []},
    }


def post(webhook: str, payload: dict[str, object]) -> None:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(  # noqa: S310 - webhook is a trusted https secret
        webhook,
        data=data,
        headers={
            "Content-Type": "application/json",
            # Discord is behind Cloudflare, which 403s (error 1010) the default
            # "Python-urllib" agent — a real User-Agent is required.
            "User-Agent": "blender-mcp-ai-changelog/1.0 (+https://github.com/harveyxiacn/blender-mcp-ai)",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            print(f"Posted to Discord (HTTP {resp.status})")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:500]
        print(f"Discord POST failed: HTTP {exc.code} {detail}")
        raise


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # emoji-safe on any console

    # Explicit argv wins over GITHUB_REF_NAME: on workflow_dispatch the latter is
    # the branch ("main"), but release.yml (tag push) has no argv so it uses the tag.
    tag = (
        (sys.argv[1] if len(sys.argv) > 1 else "") or os.environ.get("GITHUB_REF_NAME", "")
    ).strip()
    if not tag:
        print("No tag (GITHUB_REF_NAME / argv) provided; skipping.")
        return 0
    version = tag[1:] if tag.startswith("v") else tag

    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    release_url = f"{server}/{repo}/releases/tag/{tag}" if repo else server

    root = Path(__file__).resolve().parent.parent
    en = read_changelog(root / "docs" / "en" / "CHANGELOG.md", version)
    zh = read_changelog(root / "docs" / "zh" / "CHANGELOG.md", version)
    payload = build_payload(tag, en, zh, release_url)

    webhook = os.environ.get("DISCORD_CHANGELOG_WEBHOOK", "").strip()
    if not webhook:
        print("[dry-run] DISCORD_CHANGELOG_WEBHOOK not set. Would post:")
        print(json.dumps(payload, ensure_ascii=False, indent=2)[:2000])
        return 0

    post(webhook, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
