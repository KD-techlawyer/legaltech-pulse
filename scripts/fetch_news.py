#!/usr/bin/env python3
"""
Fetch legal tech news from Google News RSS feeds.
Searches configured topics, deduplicates, tags, and returns structured articles.
"""

import feedparser
import hashlib
import re
import time
import urllib.parse
from datetime import datetime, timedelta, timezone
from dateutil import parser as dateparser

# \u2500\u2500 SEARCH QUERIES \u2500\u2500
SEARCH_QUERIES = [
    "legal tech India 2026",
    "law firm AI adoption India",
    "Harvey AI legal",
    "Legora legal AI",
    "CoCounsel Thomson Reuters",
    "Khaitan OR \"Cyril Amarchand\" OR AZB technology legal",
    "legaltech startup funding 2026",
    "agentic AI legal workflows",
    "Microsoft Copilot legal",
    "Claude AI legal OR OpenAI legal OR Gemini legal OR ChatGPT legal",
    "SpotDraft OR Leegality OR CaseMine OR \"Adalat AI\" OR \"Sarvam AI\"",
    "\"Allen & Overy\" OR Goodwin OR Linklaters AI legal tech",
    "Harvey AI OR Legora OR CoCounsel OR Lucio OR \"Westlaw Edge\"",
    "contract automation AI legal 2026",
    "predictive analytics legal AI",
    "\"Shardul Amarchand\" OR JSA technology legal",
]

# \u2500\u2500 EXCLUSION PATTERNS (pure legal/regulatory \u2014 no tech angle) \u2500\u2500
EXCLUDE_PATTERNS = [
    r"\bDPDP\b", r"\bcourt judgment", r"\bcompliance news\b",
    r"\bSupreme Court\b.*\bruling\b", r"\bHigh Court\b.*\border\b",
    r"\bregulatory update\b", r"\blegislation passed\b",
    r"\bcourt order\b", r"\bjudicial review\b",
]

# \u2500\u2500 TAG RULES \u2500\u2500
TAG_RULES = [
    {
        "tag": "India Startup",
        "patterns": [
            r"SpotDraft", r"Leegality", r"CaseMine", r"Adalat AI",
            r"Sarvam AI", r"Lucio", r"India.*startup", r"Indian.*startup",
            r"legaltech.*India.*fund", r"India.*legaltech.*fund",
        ]
    },
    {
        "tag": "India Firm",
        "patterns": [
            r"Cyril Amarchand", r"Khaitan", r"AZB", r"JSA",
            r"Shardul Amarchand", r"Trilegal",
            r"Indian law firm", r"India.*law firm.*tech",
        ]
    },
    {
        "tag": "Global AI Tool",
        "patterns": [
            r"Harvey AI", r"Harvey\b", r"Legora", r"CoCounsel",
            r"Lucio", r"Westlaw Edge", r"Bloomberg Law",
            r"Claude.*legal", r"legal.*Claude", r"Copilot.*legal",
            r"legal.*Copilot", r"ChatGPT.*legal", r"legal.*ChatGPT",
            r"Gemini.*legal", r"legal.*Gemini", r"OpenAI.*legal",
            r"legal.*OpenAI", r"legal AI tool", r"legal AI platform",
            r"Spellbook", r"Anthropic.*legal",
        ]
    },
    {
        "tag": "Global Firm",
        "patterns": [
            r"Allen & Overy", r"A&O Shearman", r"Goodwin",
            r"Linklaters", r"Clifford Chance", r"Freshfields",
            r"Magic Circle", r"BigLaw.*AI", r"Am ?Law.*AI",
            r"Latham", r"Baker McKenzie",
        ]
    },
    {
        "tag": "AI Trend",
        "patterns": [
            r"agentic AI", r"AI adoption", r"AI strategy",
            r"generative AI.*legal", r"legal.*generative AI",
            r"AI.*law firm", r"law firm.*AI",
            r"foundation model", r"GPT-\d", r"Claude \d",
            r"AI agent", r"multi-model", r"AI governance",
            r"AI.*legal market", r"legal AI.*market",
        ]
    },
    {
        "tag": "Contract Tech",
        "patterns": [
            r"contract.*auto", r"CLM", r"contract lifecycle",
            r"contract review", r"contract draft",
            r"zero-touch contract", r"contract AI",
            r"DocuSign.*AI", r"Ironclad", r"Icertis",
            r"SpotDraft", r"contract management",
        ]
    },
]


def google_news_rss(query, num_results=10):
    """Fetch articles from Google News RSS for a search query."""
    encoded = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en&gl=US&ceid=US:en"
    try:
        feed = feedparser.parse(url)
        return feed.entries[:num_results]
    except Exception as e:
        print(f"  [WARN] Failed to fetch '{query}': {e}")
        return []


def parse_date(entry):
    """Parse published date from RSS entry."""
    raw = entry.get("published", entry.get("updated", ""))
    if raw:
        try:
            return dateparser.parse(raw)
        except Exception:
            pass
    return datetime.now(timezone.utc)


def dedupe_key(title):
    """Normalize title for deduplication."""
    clean = re.sub(r"[^a-z0-9 ]", "", title.lower().strip())
    clean = re.sub(r"\s+", " ", clean)
    return hashlib.md5(clean[:80].encode()).hexdigest()


def is_excluded(title, summary):
    """Check if article is purely legal/regulatory with no tech angle."""
    text = f"{title} {summary}"
    for pat in EXCLUDE_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            # Only exclude if there's no tech keyword present
            tech_keywords = r"AI|artificial intelligence|tech|automation|software|platform|tool|startup|digital"
            if not re.search(tech_keywords, text, re.IGNORECASE):
                return True
    return False


def assign_tags(title, summary):
    """Assign category tags based on content matching."""
    text = f"{title} {summary}"
    tags = []
    for rule in TAG_RULES:
        for pat in rule["patterns"]:
            if re.search(pat, text, re.IGNORECASE):
                tags.append(rule["tag"])
                break
    # Default tag if none matched
    if not tags:
        tags = ["AI Trend"]
    return list(dict.fromkeys(tags))  # dedupe preserving order


def extract_source(entry):
    """Extract source name from RSS entry."""
    source = entry.get("source", {})
    if isinstance(source, dict):
        return source.get("title", "")
    # Try to extract from title (Google News format: \"Title - Source\")
    title = entry.get("title", "")
    if " - " in title:
        return title.rsplit(" - ", 1)[-1].strip()
    return ""


def extract_title(entry):
    """Extract clean title (without source suffix)."""
    title = entry.get("title", "")
    if " - " in title:
        return title.rsplit(" - ", 1)[0].strip()
    return title


def fetch_all_stories(hours=24, max_stories=10):
    """
    Fetch stories from all configured queries.
    Returns top stories from the last `hours` hours, deduplicated and tagged.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    seen = set()
    all_articles = []

    for query in SEARCH_QUERIES:
        print(f"  Searching: {query}")
        entries = google_news_rss(query, num_results=8)
        time.sleep(0.5)  # Be polite to Google

        for entry in entries:
            title = extract_title(entry)
            if not title:
                continue

            key = dedupe_key(title)
            if key in seen:
                continue
            seen.add(key)

            pub_date = parse_date(entry)
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)

            source = extract_source(entry)
            summary = entry.get("summary", entry.get("description", ""))
            # Clean HTML from summary
            summary = re.sub(r"<[^>]+>", "", summary).strip()
            # Truncate long summaries
            if len(summary) > 400:
                summary = summary[:397] + "..."

            if is_excluded(title, summary):
                continue

            url = entry.get("link", "")
            tags = assign_tags(title, summary)

            all_articles.append({
                "title": title,
                "url": url,
                "source": source,
                "published": pub_date.strftime("%-d %b %Y"),
                "published_dt": pub_date,
                "summary": summary,
                "tags": tags,
            })

    # Sort by date descending
    all_articles.sort(key=lambda a: a["published_dt"], reverse=True)

    # Filter to last N hours for fresh stories
    fresh = [a for a in all_articles if a["published_dt"] >= cutoff]

    # Take top stories
    result = fresh[:max_stories]

    # Remove internal datetime field
    for a in result:
        del a["published_dt"]

    for a in all_articles:
        if "published_dt" in a:
            del a["published_dt"]

    return result, all_articles


if __name__ == "__main__":
    print("Fetching legal tech news...")
    fresh, all_stories = fetch_all_stories(hours=24, max_stories=10)
    print(f"\nFound {len(fresh)} fresh stories (last 24h) out of {len(all_stories)} total")
    for a in fresh:
        print(f"  [{', '.join(a['tags'])}] {a['title']}")
