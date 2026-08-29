# A single dataclass describing one internship posting.
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Internship:
    company: str
    title: str
    location: str
    url: str
    source: str  # LinkedIn | Indeed | Greenhouse | Lever | Simplify
    skills: str = ""          # comma-separated technologies/skills mentioned
    posted_date: str = ""     # when it was posted
    """Status is managed live in the sheet/dashboard and is NOT written by the
    scraper. We keep an initial value here so new rows appear with a sane
    default."""
    status: str = "Not Applied"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["scraped_at"] = datetime.now(timezone.utc).isoformat()
        return d


def _norm_url(url: str) -> str:
    """Normalize a posting URL so the same job across sources collides.

    Strips fragment/query params, trailing slashes, and lowercases — this makes
    e.g. '...?utm_source=x' and '...' resolve to the same key. Column about
    tracking params are dropped by scrapers; this is a final safety net.
    """
    if not url:
        return ""
    u = url.strip().lower()
    if "?" in u:
        u = u.split("?")[0]
    if "#" in u:
        u = u.split("#")[0]
    return u.rstrip("/")


def dedupe(internships: list[Internship]) -> list[Internship]:
    """Remove duplicates, checking both the URL and (company+title+location).

    Two kinds of duplicates are handled:
      1. Same posting with the same/normalized URL (most cross-repo overlap).
      2. Different URLs that point to the exact same (company, title, location) —
         e.g. a role listed by a new-grad repo and an internship repo with
         different apply links. The location is included so genuinely distinct
         postings (same role at a company in different cities) are NOT merged.
    """
    seen_url: set[str] = set()
    seen_sig: set[tuple] = set()
    out: list[Internship] = []
    for item in internships:
        url_key = _norm_url(item.url)
        if url_key and url_key in seen_url:
            continue
        # (company, title, location) signature catches same-role duplicates.
        sig = (
            item.company.strip().lower(),
            _norm_title(item.title),
            (item.location or "").strip().lower(),
        )
        if sig in seen_sig:
            continue
        if url_key:
            seen_url.add(url_key)
        seen_sig.add(sig)
        out.append(item)
    return out


def _norm_title(title: str) -> str:
    t = (title or "").lower()
    t = " ".join(t.split())
    return t
