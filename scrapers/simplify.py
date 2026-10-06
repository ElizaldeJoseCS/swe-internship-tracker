# Scraper for the community-maintained SimplifyJobs internship repo on GitHub.
#
# The repo README contains the internship list as HTML tables like:
#   <table><thead><tr><th>Company</th><th>Role</th><th>Location</th>
#   <th>Application</th><th>Age</th></tr></thead><tbody>
#   <tr><td><a>Company</a></td><td>Role</td><td>Location</td>
#   <td><a href="apply-url">...</a></td><td>Age</td></tr>...
#
# There are multiple category sections (SWE, Data Science, Quant, PM, etc.).
# We focus on the Software Engineering section to keep relevance high.

import re

from bs4 import BeautifulSoup

from models import Internship, dedupe
from scrapers.common import session, text_of
from config import settings

# The dev branch of the current season's repo. This is the community-updated
# source. Older seasons are archived under Summer2024-, Summer2025-, etc.
# Make this configurable via env so newer seasons don't require code edits.
from config import settings as _s
import os

DEFAULT_SIMPLIFY_REPO = os.getenv(
    "SIMPLIFY_REPO",
    "https://raw.githubusercontent.com/SimplifyJobs/Summer2025-Internships/dev/README.md",
)


def _extract_application_url(cell) -> str:
    """Find the application link in a cell, preferring an http(s) anchor."""
    for a in cell.find_all("a", href=True):
        href = a["href"]
        if href.startswith("http"):
            # Drop UTM tracking to keep stable unique keys.
            return href.split("?")[0]
    return ""


def _strip_flags(name: str) -> str:
    """Remove emoticons/flags/markers (🔥, 🛂, 🇺🇸, ↳, etc.) from a company name."""
    import unicodedata

    out = []
    for ch in name:
        cat = unicodedata.category(ch)
        # Keep letters, digits, punctuation-as-visible, spaces; drop symbols/emojis.
        if cat in ("So", "Sk", "Cf", "Mn", "Me"):
            continue
        out.append(ch)
    return "".join(out).strip()


def _clean_company(raw: str) -> str:
    name = _strip_flags(raw)
    # Continuation rows we cannot attribute are left as-is (kept minimal).
    return name


def _clean_role(raw: str) -> str:
    return " ".join(raw.split())


def _age_to_date(age: str) -> str:
    """Convert an 'Age' cell like '0d', '3d', 'New' into a YYYY-MM-DD date.

    Simplify labels entries by how many days old a posting is. We approximate
    the posted date as (today - age days). 'New'/ambiguous/blank -> ''.
    """
    from datetime import date, timedelta

    age = (age or "").strip().lower()
    m = re.match(r"^(\d+)\s*(day|d|mo|month|w|week|y|year){0,1}$", age)
    if not m:
        return ""
    num = int(m.group(1))
    unit = m.group(2)
    if not unit or unit in ("d", "day"):
        days = num
    elif unit in ("w", "week"):
        days = num * 7
    elif unit in ("mo", "month"):
        days = num * 30
    elif unit in ("y", "year"):
        days = num * 365
    else:
        days = num
    return (date.today() - timedelta(days=days)).isoformat()


def _parse_html_tables(md: str) -> list[Internship]:
    soup = BeautifulSoup(md, "lxml")
    out: list[Internship] = []

    # Pull SWE plus quant/trading sections. This lets the same source find
    # quantitative developer roles without opening unrelated PM/design tables.
    section_terms = (
        "software engineering",
        "quantitative",
        "quant",
        "trading",
        "financial engineering",
    )
    sections = soup.find_all(
        lambda tag: tag.name == "h2"
        and any(term in tag.get_text(" ", strip=True).lower() for term in section_terms)
    )
    if not sections:
        # Fall back to all tables if we can't isolate a SWE section.
        tables = soup.find_all("table")
    else:
        tables = []
        for h2 in sections:
            nxt = h2.find_next_sibling()
            # Collect subsequent tables until the next h2.
            while nxt is not None and nxt.name != "h2":
                if nxt.name == "table":
                    tables.append(nxt)
                nxt = nxt.find_next_sibling()

    for table in tables:
        last_company = ""
        for tr in table.find_all("tr"):
            cells = tr.find_all(["th", "td"])
            if len(cells) < 4:
                continue
            header = text_of(cells[0]).lower()
            if header == "company":
                continue
            company = _clean_company(text_of(cells[0]))
            if not company or company in ("↳", "/", "—", "-"):
                company = last_company
            else:
                last_company = company
            role = _clean_role(text_of(cells[1]))
            location = " | ".join(
                p.strip() for p in cells[2].get_text("\n", strip=True).splitlines() if p.strip()
            )
            # Application link lives in the 4th cell; Age is the 5th.
            url = _extract_application_url(cells[3]) if len(cells) > 3 else ""
            age = text_of(cells[4]) if len(cells) > 4 else ""
            out.append(
                Internship(
                    company=company,
                    title=role,
                    location=location,
                    url=url,
                    source="Simplify",
                    skills=role,
                    posted_date=_age_to_date(age),
                )
            )
    return out


def _parse_markdown(md: str) -> list[Internship]:
    """Table parser using BeautifulSoup (handles both HTML tables and pipe tables)."""
    return _parse_html_tables(md)


def scrape(
    repo: str = "",
    source_label: str = "Simplify",
    internship_only: bool = True,
) -> list[Internship]:
    repo = repo or os.getenv("SIMPLIFY_REPO", DEFAULT_SIMPLIFY_REPO)
    out: list[Internship] = []
    s = session()
    try:
        r = s.get(repo, timeout=settings.REQUEST_TIMEOUT)
        r.raise_for_status()
        out = _parse_html_tables(r.text)
        out = _set_source(out, source_label)
        print(f"  {source_label}: parsed {len(out)} rows from {repo}")
    except Exception as e:
        print(f"  {source_label}: failed to fetch README: {e}")
        return []

    # Keep only internship/co-op (or new-grad entries depending on mode).
    if internship_only:
        kept = [
            i
            for i in dedupe(out)
            if "intern" in i.title.lower() or "co-op" in i.title.lower()
        ]
    else:
        kept = [
            i
            for i in dedupe(out)
            if "intern" in i.title.lower()
            or "co-op" in i.title.lower()
            or "new grad" in i.title.lower()
        ]
    print(f"  {source_label}: {len(kept)} kept after filtering")
    return kept


def scrape_internships() -> list[Internship]:
    return scrape(
        repo=os.getenv(
            "SIMPLIFY_INTERNSHIP_REPO",
            "https://raw.githubusercontent.com/SimplifyJobs/Summer2025-Internships/dev/README.md",
        ),
        source_label="Simplify",
        internship_only=True,
    )


def scrape_newgrad() -> list[Internship]:
    return scrape(
        repo=os.getenv(
            "SIMPLIFY_NEWGRAD_REPO",
            "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/README.md",
        ),
        source_label="Simplify-NG",
        internship_only=False,
    )


def _set_source(items: list[Internship], label: str) -> list[Internship]:
    for i in items:
        i.source = label
    return items
