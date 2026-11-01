#!/usr/bin/env python3
"""Download a GitHub issue's body, comments and file attachments for scanning.

GitHub's native GitGuardian integration does NOT scan issue attachments, so we
fetch them here and hand them to ggshield / the GitGuardian API.

Usage:
    python scan_issue_attachments.py --repo owner/repo --issue 123 --out /tmp/gg-scan
"""
import argparse
import os
import re
import sys
import urllib.request
import urllib.error
import json
from pathlib import Path

GITHUB_API = "https://api.github.com"


def gh_request(url, token):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def download(url, dest, token):
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            data = resp.read()
        dest.write_bytes(data)
        return True
    except Exception as e:  # noqa: BLE001
        print(f"  ! could not download {url}: {e}", file=sys.stderr)
        return False


def safe_name(s):
    return re.sub(r"[^A-Za-z0-9._-]", "_", s)[:120] or "file"


def extract_attachment_urls(text):
    """Find file attachment URLs in issue/comment markdown."""
    urls = set()
    if not text:
        return urls
    # Markdown images/links: ![alt](url) and [text](url)
    for m in re.finditer(r"\]\((https?://[^\s)]+)\)", text):
        u = m.group(1)
        if any(h in u for h in ("github.com", "githubusercontent.com", "user-attachments")):
            urls.add(u)
    # Bare URLs on their own line
    for m in re.finditer(r"https?://\S+", text):
        u = m.group(0).rstrip(").,")
        if "user-attachments" in u or "/files/" in u or "github.com" in u:
            urls.add(u)
    return urls


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="owner/repo")
    ap.add_argument("--issue", required=True, type=int)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    issue = gh_request(f"{GITHUB_API}/repos/{args.repo}/issues/{args.issue}", token)
    # Save issue body
    (out / "issue_body.txt").write_text(issue.get("body") or "", encoding="utf-8")
    print(f"Issue #{args.issue}: {issue.get('title')}")

    all_text = [issue.get("body") or ""]
    attachment_urls = extract_attachment_urls(issue.get("body"))

    # Comments
    comments = gh_request(f"{GITHUB_API}/repos/{args.repo}/issues/{args.issue}/comments", token)
    for i, c in enumerate(comments):
        (out / f"comment_{i+1}.txt").write_text(c.get("body") or "", encoding="utf-8")
        all_text.append(c.get("body") or "")
        attachment_urls |= extract_attachment_urls(c.get("body"))

    # Download attachments
    att_dir = out / "attachments"
    att_dir.mkdir(exist_ok=True)
    for idx, url in enumerate(sorted(attachment_urls), 1):
        name = safe_name(url.split("/")[-1].split("?")[0]) or f"attachment_{idx}"
        dest = att_dir / f"{idx:03d}_{name}"
        print(f"  downloading {url}")
        download(url, dest, token)

    print(f"Saved issue content + {len(list(att_dir.iterdir()))} attachments to {out}")


if __name__ == "__main__":
    main()
