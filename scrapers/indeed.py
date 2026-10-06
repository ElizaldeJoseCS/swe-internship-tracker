# Scraper for Indeed job search results.
#
# Like LinkedIn, Indeed gates scraping behind bot detection. We target the
# generic search results page which works without a login for simple queries:
#
#   https://www.indeed.com/jobs?q=software+engineering+internship&fromage=14
#
# Results are rendered in HTML (job cards in <a class="jcs-JobTitle">) plus a
# JSON blob inside the script tag `window._initialData`. We parse the HTML
# cards, which is the most robust cross-page approach.
#
# If Indeed blocks you (403 / captcha), consider supplying a session cookie or
# using a residential proxy; see .env.example (# INDEED settings).

from urllib.parse import quote

from models import Internship, dedupe
from scrapers.common import get_soup, text_of
from config import settings


def _build_url(query: str = "software engineering internship") -> str:
    base = "https://www.indeed.com/jobs"
    return f"{base}?q={quote(query)}&l=&fromage=14&start=0"


def _parse_cards(soup) -> list[Internship]:
    out = []
    # Historically the result is in <div class="job_seen_beacon"> with a title
    # link inside. Some layout versions differ; we select by the title class.
    for card in soup.select("div.job_seen_beacon, div.result, div.jobsearch-SerpJobCard"):
        title_el = card.select_one("a.jcs-JobTitle, h2.jobTitle a")
        if not title_el:
            continue
        title = text_of(title_el)
        if not title or "intern" not in title.lower():
            continue
        url = title_el.get("href") or ""
        if url and url.startswith("/"):
            url = "https://www.indeed.com" + url
        comp_el = card.select_one('span[data-testid="company-name"], span.company')
        loc_el = card.select_one('div[data-testid="text-location"], div.companyLocation')
        out.append(
            Internship(
                company=text_of(comp_el),
                title=title,
                location=text_of(loc_el),
                url=url,
                source="Indeed",
                skills=title,
            )
        )
    return out


def scrape(query: str = "software engineering internship") -> list[Internship]:
    url = _build_url(query)
    print(f"  Indeed: scraping {url}")
    try:
        soup = get_soup(url)
    except Exception as e:
        print(f"  Indeed: fetch failed: {e}")
        return []
    out = _parse_cards(soup)
    print(f"  Indeed: {len(out)} internship cards parsed")
    return dedupe(out)
