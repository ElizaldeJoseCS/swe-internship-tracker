# Scraper for GameJobs.co — a dedicated game-industry job board.
#
# Two options here, both login-free:
#   1. The Atom feed (https://gamejobs.co/?format=atom), which paginates cleanly
#      and gives title + company + URL without hammering the detail pages.
#   2. The HTML listing page(s) with company in the URL slug.
#
# We use the Atom feed since it's fast and returns the most jobs per request.
# Titles are formatted as "<Role> at <Company>"; we split on " at " to fill the
# Company/Title columns.

import re
from urllib.parse import urljoin
from xml.etree import ElementTree as ET

from models import Internship, dedupe
from scrapers.common import fetch
from config import settings

BASE = "https://gamejobs.co"
FEED_URL = BASE + "/?format=atom"

# Only postings with "engineer"/"software" are kept; strip out art/design/marketing
# unless the user wants everything. Keeps results focused on SWE.
DEFAULT_JOB_TERMS = [
    "software engineer", "software engineering", "gameplay engineer",
    "engine programmer", "programmer", "tools engineer", "backend",
    "back end", "frontend", "front end", "full stack", "fullstack",
    "devops", "game server", "data engineer", "ml engineer", "machine learning",
    "graphics", "network engineer", "systems engineer", "automation",
]


def _parse_feed(xml_text: str) -> list[dict]:
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_text)
    entries = []
    for entry in root.findall("a:entry", ns):
        title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip()
        link_el = entry.find("a:link", ns)
        href = link_el.get("href") if link_el is not None else ""
        updated = entry.findtext("a:updated", default="", namespaces=ns) or ""
        entries.append({"title": title, "url": urljoin(BASE, href), "updated": updated})
    return entries


def _split_title(title: str):
    """Return (role, company) from a title like 'X at Y'."""
    m = re.search(r"\s+at\s+", title)
    if m:
        role = title[: m.start()].strip()
        company = title[m.end():].strip()
        return role, company
    return title, ""


def scrape() -> list[Internship]:
    out: list[Internship] = []
    page = 1
    active_terms = [t for t in DEFAULT_JOB_TERMS]

    # Decide whether to keep non-SWE roles.
    keep_all = settings.GAME_KEEP_ALL

    while page <= settings.GAME_MAX_PAGES:
        url = f"{FEED_URL}&p={page}" if page > 1 else FEED_URL
        try:
            resp = fetch(url)
        except Exception:
            break
        entries = _parse_feed(resp.text)
        if not entries:
            break
        for e in entries:
            role, company = _split_title(e["title"])
            low = role.lower()
            if not keep_all and not any(t in low for t in active_terms):
                continue
            # Filter to internship/co-op if configured (default true).
            if settings.FILTER_TITLES and not ("intern" in low or "co-op" in low):
                continue
            out.append(
                Internship(
                    company=company or "?",
                    title=role,
                    location="",
                    url=e["url"],
                    source="GameJobs",
                    skills=role,
                    posted_date=(e["updated"] or "")[:10],
                )
            )
        page += 1

    print(f"  GameJobs: {len(out)} SWE-ish postings parsed")
    return dedupe(out)