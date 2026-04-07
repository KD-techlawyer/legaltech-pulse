#!/usr/bin/env python3
"""
Daily LegalTech Pulse updater.

Orchestrates the full pipeline:
1. Load existing data from index.html
2. Fetch new stories from Google News RSS
3. Move old fresh stories to archive
4. Deduplicate against existing archive
5. Regenerate the full site (index.html + category pages)
"""

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from fetch_news import fetch_all_stories, dedupe_key
from generate_site import generate_site, load_briefing_data


def merge_stories(existing_data, new_articles, max_fresh=10):
    """
    Merge new articles into existing data:
    - New articles become the fresh 'articles' section
    - Previous fresh articles move to archive
    - Deduplicate across everything
    """
    old_fresh = existing_data.get("articles", [])
    old_archive = existing_data.get("archive", [])

    # Build dedup set from new articles
    new_keys = set()
    for a in new_articles:
        new_keys.add(dedupe_key(a["title"]))

    # Move old fresh to archive (if not duplicates of new)
    for a in old_fresh:
        key = dedupe_key(a["title"])
        if key not in new_keys:
            old_archive.insert(0, a)  # prepend to archive

    # Deduplicate archive
    seen = set()
    deduped_archive = []
    for a in old_archive:
        key = dedupe_key(a["title"])
        if key not in seen and key not in new_keys:
            seen.add(key)
            deduped_archive.append(a)

    # Cap archive at 200 stories to keep file manageable
    deduped_archive = deduped_archive[:200]

    return {
        "date": datetime.now(timezone.utc).strftime("%A, %-d %B %Y"),
        "articles": new_articles[:max_fresh],
        "archive": deduped_archive,
    }


def main():
    print("=" * 60)
    print("LegalTech Pulse \u2014 Daily Update")
    print(f"Date: {datetime.now(timezone.utc).strftime('%A, %-d %B %Y %H:%M UTC')}")
    print("=" * 60)

    # Step 1: Load existing data
    index_path = os.path.join(REPO_ROOT, "index.html")
    if os.path.exists(index_path):
        print("\n[1/4] Loading existing data from index.html...")
        try:
            existing_data = load_briefing_data(index_path)
            print(f"  Found {len(existing_data.get('articles', []))} fresh + {len(existing_data.get('archive', []))} archived stories")
        except Exception as e:
            print(f"  [WARN] Could not parse existing data: {e}")
            existing_data = {"articles": [], "archive": []}
    else:
        print("\n[1/4] No existing index.html found, starting fresh")
        existing_data = {"articles": [], "archive": []}

    # Step 2: Fetch new stories
    print("\n[2/4] Fetching new stories from Google News RSS...")
    new_articles, all_found = fetch_all_stories(hours=24, max_stories=10)
    print(f"  Found {len(new_articles)} new stories (last 24h)")

    if not new_articles:
        print("\n  No new stories found. Keeping existing data.")
        # Still regenerate site (in case template changed)
        new_articles = existing_data.get("articles", [])
        merged = existing_data
        merged["date"] = datetime.now(timezone.utc).strftime("%A, %-d %B %Y")
    else:
        # Step 3: Merge and archive
        print("\n[3/4] Merging stories and archiving old ones...")
        merged = merge_stories(existing_data, new_articles)
        print(f"  Fresh: {len(merged['articles'])} | Archive: {len(merged['archive'])}")

    # Step 4: Generate site
    print("\n[4/4] Generating site...")
    generate_site(merged)

    # Also save raw data as JSON for debugging/backup
    data_path = os.path.join(REPO_ROOT, "data", "briefing.json")
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    with open(data_path, "w") as f:
        json.dump(merged, f, indent=2)
    print(f"  Saved data backup: data/briefing.json")

    print("\n" + "=" * 60)
    print("Update complete!")
    total = len(merged["articles"]) + len(merged["archive"])
    print(f"Total stories: {total} ({len(merged['articles'])} fresh, {len(merged['archive'])} archive)")
    print("=" * 60)


if __name__ == "__main__":
    main()
