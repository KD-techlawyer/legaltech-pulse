#!/usr/bin/env python3
"""
Generate the LegalTech Pulse website:
- index.html (main page with all stories)
- pages/<category>.html (one page per tag category)
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES_DIR = os.path.join(REPO_ROOT, "pages")

# Category slug mapping
CATEGORY_SLUGS = {
    "Global AI Tool": "global-ai-tool",
    "AI Trend": "ai-trend",
    "Contract Tech": "contract-tech",
    "Global Firm": "global-firm",
    "India Startup": "india-startup",
    "India Firm": "india-firm",
}

CSS = """:root {
    --bg: #faf8f5;
    --surface: #ffffff;
    --surface-hover: #f5f2ee;
    --border: #e5e0d8;
    --accent: #5a4fcf;
    --accent-glow: rgba(90,79,207,0.08);
    --text: #3d3a36;
    --text-dim: #78736b;
    --text-bright: #1a1816;
    --tag-india: #0d9668;
    --tag-global: #2563eb;
    --tag-ai: #d97706;
    --tag-firm: #db2777;
    --tag-trend: #7c3aed;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    min-height: 100vh;
  }

  .container {
    max-width: 900px;
    margin: 0 auto;
    padding: 2rem 1.5rem;
  }

  /* Header */
  .header {
    text-align: center;
    margin-bottom: 2.5rem;
    padding-bottom: 2rem;
    border-bottom: 1px solid var(--border);
  }
  .header h1 {
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-bright);
    letter-spacing: -0.5px;
  }
  .header h1 span { color: var(--accent); }
  .header h1 a { color: inherit; text-decoration: none; }
  .header h1 a span { color: var(--accent); }
  .header .subtitle {
    color: var(--text-dim);
    font-size: 0.95rem;
    margin-top: 0.5rem;
  }
  .header .date {
    display: inline-block;
    margin-top: 0.75rem;
    padding: 0.3rem 1rem;
    background: var(--accent-glow);
    border: 1px solid rgba(90,79,207,0.2);
    border-radius: 20px;
    font-size: 0.85rem;
    color: var(--accent);
    font-weight: 500;
  }

  /* Nav */
  .nav {
    display: flex;
    gap: 0.5rem;
    justify-content: center;
    margin-bottom: 2rem;
    flex-wrap: wrap;
  }
  .nav a {
    font-size: 0.8rem;
    font-weight: 500;
    padding: 0.35rem 0.8rem;
    border-radius: 6px;
    text-decoration: none;
    color: var(--text-dim);
    border: 1px solid var(--border);
    transition: all 0.2s;
  }
  .nav a:hover, .nav a.active {
    color: var(--accent);
    border-color: var(--accent);
    background: var(--accent-glow);
  }
  .nav a .count {
    font-weight: 700;
    color: var(--text-bright);
    margin-right: 0.25rem;
  }
  .nav a.active .count {
    color: var(--accent);
  }

  /* Stats bar */
  .stats {
    display: flex;
    gap: 1.5rem;
    justify-content: center;
    margin-bottom: 2rem;
    flex-wrap: wrap;
  }
  .stat {
    font-size: 0.82rem;
    color: var(--text-dim);
  }
  .stat strong {
    color: var(--text-bright);
    font-size: 1.1rem;
  }

  /* Section headers */
  .section-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 2rem 0 1rem;
  }
  .section-header h3 {
    font-size: 0.85rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--accent);
    white-space: nowrap;
  }
  .section-header .line {
    flex: 1;
    height: 1px;
    background: var(--border);
  }
  .section-header .count {
    font-size: 0.75rem;
    color: var(--text-dim);
    font-weight: 400;
    text-transform: none;
    letter-spacing: 0;
  }

  /* Article card */
  .article {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s, background 0.2s, box-shadow 0.2s;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }
  .article:hover {
    border-color: var(--accent);
    background: var(--surface-hover);
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  }
  .article-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 0.6rem;
  }
  .article h2 {
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--text-bright);
    line-height: 1.4;
  }
  .article h2 a {
    color: inherit;
    text-decoration: none;
  }
  .article h2 a:hover { color: var(--accent); }
  .article .meta {
    font-size: 0.78rem;
    color: var(--text-dim);
    white-space: nowrap;
    flex-shrink: 0;
    text-align: right;
    line-height: 1.5;
  }
  .article .meta .pub-date {
    font-weight: 500;
    color: var(--accent);
    font-size: 0.74rem;
  }
  .article .summary {
    font-size: 0.9rem;
    color: var(--text-dim);
    margin-bottom: 0.8rem;
    line-height: 1.55;
  }
  .tags { display: flex; gap: 0.4rem; flex-wrap: wrap; }
  .tag {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    background: transparent;
  }
  .tag-india { color: var(--tag-india); border: 1px solid rgba(13,150,104,0.25); background: rgba(13,150,104,0.06); }
  .tag-global { color: var(--tag-global); border: 1px solid rgba(37,99,235,0.25); background: rgba(37,99,235,0.06); }
  .tag-ai { color: var(--tag-ai); border: 1px solid rgba(217,119,6,0.25); background: rgba(217,119,6,0.06); }
  .tag-firm { color: var(--tag-firm); border: 1px solid rgba(219,39,119,0.25); background: rgba(219,39,119,0.06); }
  .tag-trend { color: var(--tag-trend); border: 1px solid rgba(124,58,237,0.25); background: rgba(124,58,237,0.06); }

  /* Archive articles — slightly muted */
  .archive-section .article {
    opacity: 0.8;
  }
  .archive-section .article:hover {
    opacity: 1;
  }

  /* Footer */
  .footer {
    text-align: center;
    padding-top: 2rem;
    margin-top: 1rem;
    border-top: 1px solid var(--border);
    font-size: 0.8rem;
    color: var(--text-dim);
  }

  /* Empty state */
  .empty {
    text-align: center;
    padding: 3rem 1rem;
    color: var(--text-dim);
  }
  .empty .icon { font-size: 2.5rem; margin-bottom: 1rem; }"""


def tag_class(tag):
    t = tag.lower()
    if "india" in t:
        return "india"
    if "global" in t:
        return "global"
    if "ai" in t or "tool" in t:
        return "ai"
    if "firm" in t:
        return "firm"
    return "trend"


def escape_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def render_article_card(article):
    title = escape_html(article["title"])
    url = article.get("url", "#")
    source = escape_html(article.get("source", ""))
    published = escape_html(article.get("published", ""))
    summary = escape_html(article.get("summary", ""))
    tags_html = "".join(
        f'<span class="tag tag-{tag_class(t)}">{escape_html(t)}</span>'
        for t in article.get("tags", [])
    )
    return f"""    <div class="article">
      <div class="article-header">
        <h2><a href="{url}" target="_blank" rel="noopener">{title}</a></h2>
        <div class="meta">{source}<br><span class="pub-date">{published}</span></div>
      </div>
      <div class="summary">{summary}</div>
      <div class="tags">{tags_html}</div>
    </div>"""


def build_nav_html(tag_counts, active_category=None, base_path=""):
    """Build navigation bar with category links."""
    links = []
    # All stories link
    total = sum(tag_counts.values())
    cls = ' class="active"' if active_category is None else ''
    links.append(f'<a href="{base_path}index.html"{cls}><span class="count">{total}</span>All Stories</a>')

    for tag_name, slug in CATEGORY_SLUGS.items():
        count = tag_counts.get(tag_name, 0)
        if count == 0:
            continue
        cls = ' class="active"' if active_category == tag_name else ''
        links.append(f'<a href="{base_path}pages/{slug}.html"{cls}><span class="count">{count}</span>{escape_html(tag_name)}</a>')

    return "\n    ".join(links)


def generate_page(title, subtitle, date_str, nav_html, sections, base_path=""):
    """Generate a complete HTML page."""
    sections_html = ""
    for section in sections:
        label = section["label"]
        articles = section["articles"]
        extra_class = section.get("class", "")
        if not articles:
            continue

        wrapper_open = f'<div class="{extra_class}">' if extra_class else ""
        wrapper_close = "</div>" if extra_class else ""

        cards = "\n".join(render_article_card(a) for a in articles)
        sections_html += f"""
  {wrapper_open}
  <div class="section-header">
    <h3>{label} <span class="count">({len(articles)} stories)</span></h3>
    <div class="line"></div>
  </div>
  {cards}
  {wrapper_close}
"""

    if not sections_html.strip():
        sections_html = '<div class="empty"><div class="icon">No stories found for this category yet.</div></div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape_html(title)}</title>
<style>
{CSS}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1><a href="{base_path}index.html">LegalTech <span>Pulse</span></a></h1>
    <div class="subtitle">{escape_html(subtitle)}</div>
    <div class="date">{escape_html(date_str)}</div>
  </div>

  <div class="nav">
    {nav_html}
  </div>

  {sections_html}

  <div class="footer">
    Auto-generated by LegalTech Pulse &middot; Powered by Claude
  </div>
</div>
</body>
</html>
"""


def load_briefing_data(filepath):
    """Load BRIEFING_DATA from index.html or a JSON file."""
    if filepath.endswith(".json"):
        with open(filepath) as f:
            return json.load(f)

    # Parse from index.html
    with open(filepath) as f:
        content = f.read()

    match = re.search(r"const BRIEFING_DATA\s*=\s*(\{.*?\});\s*\n", content, re.DOTALL)
    if not match:
        print("ERROR: Could not find BRIEFING_DATA in index.html")
        sys.exit(1)

    return json.loads(match.group(1))


def compute_tag_counts(articles, archive):
    """Count articles per tag across all stories."""
    counts = {}
    for a in articles + archive:
        for tag in a.get("tags", []):
            counts[tag] = counts.get(tag, 0) + 1
    return counts


def generate_site(data, output_dir=None):
    """Generate the full site: index.html + category pages."""
    if output_dir is None:
        output_dir = REPO_ROOT

    articles = data.get("articles", [])
    archive = data.get("archive", [])
    date_str = data.get("date", datetime.now(timezone.utc).strftime("%A, %-d %B %Y"))
    all_stories = articles + archive

    tag_counts = compute_tag_counts(articles, archive)

    # ── Main page (index.html) ──
    nav_html = build_nav_html(tag_counts, active_category=None, base_path="")
    main_sections = [
        {"label": "Fresh (last 48h)", "articles": articles, "class": ""},
        {"label": "Earlier", "articles": archive, "class": "archive-section"},
    ]
    main_html = generate_page(
        title="LegalTech Pulse — Morning Briefing",
        subtitle="Morning Briefing",
        date_str=date_str,
        nav_html=nav_html,
        sections=main_sections,
        base_path="",
    )
    index_path = os.path.join(output_dir, "index.html")
    with open(index_path, "w") as f:
        f.write(main_html)
    print(f"  Generated: index.html ({len(articles)} fresh, {len(archive)} archive)")

    # ── Category pages ──
    pages_dir = os.path.join(output_dir, "pages")
    os.makedirs(pages_dir, exist_ok=True)

    for tag_name, slug in CATEGORY_SLUGS.items():
        count = tag_counts.get(tag_name, 0)
        if count == 0:
            continue

        # Filter stories with this tag
        cat_fresh = [a for a in articles if tag_name in a.get("tags", [])]
        cat_archive = [a for a in archive if tag_name in a.get("tags", [])]

        nav_html = build_nav_html(tag_counts, active_category=tag_name, base_path="../")
        sections = [
            {"label": f"Fresh — {tag_name}", "articles": cat_fresh, "class": ""},
            {"label": f"Earlier — {tag_name}", "articles": cat_archive, "class": "archive-section"},
        ]

        page_html = generate_page(
            title=f"{tag_name} — LegalTech Pulse",
            subtitle=f"{tag_name}",
            date_str=date_str,
            nav_html=nav_html,
            sections=sections,
            base_path="../",
        )

        page_path = os.path.join(pages_dir, f"{slug}.html")
        with open(page_path, "w") as f:
            f.write(page_html)
        print(f"  Generated: pages/{slug}.html ({len(cat_fresh)} fresh, {len(cat_archive)} archive)")


if __name__ == "__main__":
    data_source = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO_ROOT, "index.html")
    print(f"Loading data from: {data_source}")
    data = load_briefing_data(data_source)
    print("Generating site...")
    generate_site(data)
    print("Done!")
