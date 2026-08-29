# Scraper for LinkedIn job search results.
#
# LinkedIn heavily gates scraping behind login and bot detection. A fully
# automated, login-based scraper is fragile and against their ToS; the most
# reliable no-auth approach is to parse the public (guest) jobs search page:
#
#   https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?...
#
# This returns HTML cards. Note: LinkedIn or proxies may still show a captcha.
# If you get zero results / blocked, switch to using your LinkedIn cookie
# (export a session) via the LINKEDIN_COOKIE env var described in .env.example.
#
# When provided, we pass a logged-in session cookie so results are richer and
# bot checks are far less likely.

from urllib.parse import quote

from models import Internship, dedupe
from scrapers.common import get_soup, text_of
from config import settings
import os


def _base_url() -> str:
    return "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"


def _build_url(query: str = "software engineering internship") -> str:
    params = (
        f"?keywords={quote(query)}&location=United%20States"
        "&f_JT=I"  # filter: internship job type
        "&start=0"
    )
    return _base_url() + params


def _parse_cards(soup) -> list[Internship]:
    out = []
    cards = soup.select("div.base-card") or soup.select("li")
    for card in cards:
        link = card.select_one("a.base-card__full-link")
        if not link:
            continue
        url = link.get("href") or ""
        # Strip tracking/position query params so the URL is a stable unique key
        # (important so statuses persist across re-scrapes).
        url = url.split("?")[0]
        title_el = card.select_one("h3.base-search-card__title")
        comp_el = card.select_one("h4.base-search-card__subtitle")
        loc_el = card.select_one("span.job-search-card__location")
        title = text_of(title_el)
        if not title or "intern" not in title.lower():
            continue
        out.append(
            Internship(
                company=text_of(comp_el),
                title=title,
                location=text_of(loc_el),
                url=url,
                source="LinkedIn",
                skills=title,
            )
        )
    return out


def scrape(query: str = "software engineering internship") -> list[Internship]:
    headers = {}
    cookie = os.getenv("LINKEDIN_COOKIE", "")
    if cookie:
        headers["Cookie"] = cookie
    url = _build_url(query)
    print(f"  LinkedIn: scraping {url}")
    try:
        soup = get_soup(url, headers=headers)
    except Exception as e:
        print(f"  LinkedIn: fetch failed: {e}")
        return []
    out = _parse_cards(soup)
    print(f"  LinkedIn: {len(out)} internship cards parsed")
    return dedupe(out)
