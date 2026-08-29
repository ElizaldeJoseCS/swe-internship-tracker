# Scraper for Lever ATS internship postings.
#
# Lever exposes a public JSON endpoint per company:
#   GET https://api.lever.co/v0/postings/{company}?mode=json
# The company identifier is the slug in a jobs URL like
# https://jobs.lever.co/acme   (board "acme")
#
# User supplies comma-separated board slugs in LEVER_BOARDS.

import re

from models import Internship, dedupe
from scrapers.common import session
from config import settings


def _clean(html: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", html or "").split())


def _keywords(*chunks: str) -> str:
    known = [
        "python", "java", "javascript", "typescript", "go", "golang", "c++", "c#",
        "ruby", "rust", "kotlin", "swift", "sql", "postgres", "mysql", "mongodb",
        "react", "angular", "vue", "node", "django", "flask", "fastapi", "spring",
        "aws", "azure", "gcp", "docker", "kubernetes", "k8s", "machine learning",
        "ml", "tensorflow", "pytorch", "graphql", "redis", "kafka", "terraform",
        "linux", "git", "ci/cd", "rest", "api", "backend", "frontend", "fullstack",
    ]
    haystack = " ".join(chunks).lower()
    return ", ".join(dict.fromkeys(k for k in known if k in haystack))


def scrape() -> list[Internship]:
    out: list[Internship] = []
    s = session()
    boards = [b for b in settings.LEVER_BOARDS]
    if not boards:
        print("  Lever: no boards configured (set LEVER_BOARDS)")
        return out

    for board in boards:
        # Accept either "acme" or "https://jobs.lever.co/acme"
        slug = board.strip().rstrip("/").split("/")[-1]
        url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
        try:
            r = s.get(url, timeout=settings.REQUEST_TIMEOUT)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"  Lever: error for board '{board}': {e}")
            continue

        if not isinstance(data, list):
            print(f"  Lever: unexpected payload for '{board}'")
            continue

        for job in data:
            title = (job.get("text") or "").strip()
            if not title or not ("intern" in title.lower() or "co-op" in title.lower()):
                continue
            locs = job.get("categories", {}).get("location", "") or ""
            desc = job.get("description", "") or ""
            hosted = job.get("hostedUrl") or job.get("applyUrl") or ""
            out.append(
                Internship(
                    company=(job.get("company") or slug).title(),
                    title=title,
                    location=locs,
                    url=hosted,
                    source="Lever",
                    skills=_keywords(title, desc, locs),
                    posted_date=job.get("createdAt", "") or "",
                )
            )
        print(f"  Lever: processed board '{board}'")

    return dedupe(out)
