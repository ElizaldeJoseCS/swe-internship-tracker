# Scraper for Greenhouse ATS internship postings.
#
# Greenhouse exposes a public, unauthenticated JSON API per company board:
#   GET https://boards-api.greenhouse.io/v1/boards/{board}/jobs
# Returns { job: { id, title, content, location, absolute_url, ... } }
#
# Because there are thousands of boards, the user must supply a comma-separated
# list of company names in GREENHOUSE_BOARDS (see config/.env).

import json
import requests

from models import Internship, dedupe
from scrapers.common import session
from config import settings


def _clean(content_html: str) -> str:
    """Extract plain-text skills/tech keywords from the job's HTML content."""
    import re

    text = re.sub(r"<[^>]+>", " ", content_html or "")
    return " ".join(text.split())


def _keywords(title: str, content: str, location: str) -> str:
    """Collect useful 'skills looking for' keywords as a hint.

    This is a light keyword extractor; it captures common tech terms so the
    sheet gets a rough 'skills' column without heavy NLP.
    """
    known = [
        "python", "java", "javascript", "typescript", "go", "golang", "c++", "c#",
        "ruby", "rust", "kotlin", "swift", "sql", "postgres", "mysql", "mongodb",
        "react", "angular", "vue", "node", "django", "flask", "fastapi", "spring",
        "aws", "azure", "gcp", "docker", "kubernetes", "k8s", "machine learning",
        "ml", "tensorflow", "pytorch", "react-native", "graphql", "redis", "kafka",
        "terraform", "linux", "git", "ci/cd", "rest", "api",
    ]
    haystack = f"{title} {content} {location}".lower()
    found = []
    for kw in known:
        if kw in haystack:
            found.append(kw)
    return ", ".join(dict.fromkeys(found))


def scrape() -> list[Internship]:
    out: list[Internship] = []
    s = session()
    boards = [b for b in settings.GREENHOUSE_BOARDS]
    if not boards:
        print("  Greenhouse: no boards configured (set GREENHOUSE_BOARDS)")
        return out

    for board in boards:
        board = board.strip().lower().replace("https://boards.greenhouse.io/", "")
        url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs"
        try:
            r = s.get(url, timeout=settings.REQUEST_TIMEOUT)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"  Greenhouse: error for board '{board}': {e}")
            continue

        for job in data.get("jobs", []):
            title = (job.get("title") or "").strip()
            if not title or not any(term in title.lower() for term in ("intern", "co-op", "new grad", "new-grad", "entry level", "entry-level", "junior")):
                continue
            loc = job.get("location") or {}
            location = loc.get("name") if isinstance(loc, dict) else str(loc or "")
            content = job.get("content") or ""
            out.append(
                Internship(
                    company=board.title(),
                    title=title,
                    location=location,
                    url=job.get("absolute_url") or "",
                    source="Greenhouse",
                    skills=_keywords(title, content, location),
                    posted_date=job.get("updated_at", "") or "",
                )
            )
        print(f"  Greenhouse: {board} -> {sum(1 for x in out if x.company.lower()==board)} matched")

    return dedupe(out)
