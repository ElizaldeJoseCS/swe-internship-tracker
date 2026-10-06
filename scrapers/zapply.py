# Scraper for the zapplyjobs/New-Grad-Jobs-2027 GitHub repo.
#
# This repo lists jobs as markdown pipe tables grouped under collapsible
# <details><summary><h3>Category</h3></summary> sections. Only the
# "Software Engineering" category interests us (we keep it SWE-focused).
#
# Row format:
#   | **Company** | Role | Location | Posted | Visa | [<img Apply>](url) |
# The apply URL is the (url) in the last cell's markdown link.

import re
import html as _html

import requests

from models import Internship, dedupe
from config import settings

REPO = "https://raw.githubusercontent.com/zapplyjobs/New-Grad-Jobs-2027/main/README.md"

# Category heading text (stripped of HTML) we actually want.
WANTED_CATEGORIES = ["software engineering"]

# Apply-link cell patterns to extract the URL.
_apply_re = re.compile(r"\]\((https?://[^)]+)\)")

# Marks the end of a section's table (the pipe-table separator row).
_sep_re = re.compile(r"^\|[\s|:-]+$")


def _extract_url(cell: str) -> str:
    m = _apply_re.search(cell)
    if m:
        # Drop UTM/tracking params for a stable unique key.
        return m.group(1).split("?")[0]
    return ""


def _clean_company(raw: str) -> str:
    s = re.sub(r"[*_`]+", "", raw or "").strip()
    return s


def _split_pipe_row(line: str) -> list[str]:
    line = line.strip()
    if not line.startswith("|"):
        return []
    line = line.strip("|")
    return [c.strip() for c in line.split("|")]


def _parse_sections(md: str) -> list[Internship]:
    out: list[Internship] = []
    # Iterate over lines; track which category we're in based on <summary><h3>.
    current_cat = ""
    in_wanted = False
    for line in md.splitlines():
        # Detect a new category header.
        sm = re.search(r"<summary><h3>(.*?)</h3>", line)
        if sm:
            label = re.sub(r"<[^>]+>|\d+\.", "", sm.group(1)).strip()
            current_cat = _html.unescape(label).lower()
            in_wanted = any(w in current_cat for w in WANTED_CATEGORIES)
            continue
        if not in_wanted:
            continue
        # Skip the table header + separator rows.
        if line.lstrip().startswith("| Company") or _sep_re.match(line.strip()):
            continue
        if not line.lstrip().startswith("|"):
            continue
        cells = _split_pipe_row(line)
        if len(cells) < 4:
            continue
        company = _clean_company(cells[0])
        role = cells[1]
        location = cells[2]
        posted = cells[3]
        # Apply URL is in the last cell (index 4 or 5).
        url = _extract_url(cells[-1])
        if not url:
            continue
        out.append(
            Internship(
                company=company,
                title=role,
                location=location,
                url=url,
                source="Zapply",
                skills=role,
                posted_date=posted,
            )
        )
    return out


def scrape() -> list[Internship]:
    s = requests.Session()
    s.headers["User-Agent"] = settings.USER_AGENT
    try:
        r = s.get(REPO, timeout=settings.REQUEST_TIMEOUT)
        r.raise_for_status()
    except Exception as e:
        print(f"  Zapply: failed to fetch: {e}")
        return []

    out = _parse_sections(r.text)
    # Keep internship/co-op/new-grad software roles.
    kept = [
        i
        for i in dedupe(out)
        if "intern" in i.title.lower()
        or "co-op" in i.title.lower()
        or "new grad" in i.title.lower()
    ]
    print(f"  Zapply: parsed {len(out)} SWE rows, kept {len(kept)}")
    return kept
