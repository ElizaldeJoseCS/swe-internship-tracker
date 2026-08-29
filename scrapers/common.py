# Shared helpers used by every scraper: HTTP session + relevance filtering.
import requests
from bs4 import BeautifulSoup

from config import settings


def session() -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": settings.USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
    )
    return s


def fetch(url: str, **kwargs) -> requests.Response:
    """Fetch a URL with the default timeout and a UA header."""
    s = session()
    kwargs.setdefault("timeout", settings.REQUEST_TIMEOUT)
    try:
        resp = s.get(url, **kwargs)
        resp.raise_for_status()
        return resp
    except requests.RequestException as e:
        print(f"  ! fetch failed for {url}: {e}")
        raise


def get_soup(url: str, **kwargs) -> BeautifulSoup:
    resp = fetch(url, **kwargs)
    return BeautifulSoup(resp.text, "lxml")


def is_sw_internship(item) -> bool:
    """Heuristic filter: does this posting look like a software internship?

    `item` may be an Internship model or a duck-typed object with .title and
    .skills attributes. Also supports passing a plain string.
    """
    text = ""
    if isinstance(item, str):
        text = item
    else:
        chunks = [getattr(item, "title", "") or ""]
        if getattr(item, "skills", None):
            chunks.append(item.skills)
        text = " ".join(chunks).lower()

    text = text or ""
    if settings.FILTER_TITLES and "intern" not in text and "co-op" not in text:
        return False

    if settings.TARGET_COMPANIES:
        # If the user specified companies, keep only those.
        haystack = text
        if not isinstance(item, str):
            haystack = (getattr(item, "company", "") or "").lower()
        if not any(c in haystack for c in settings.TARGET_COMPANIES):
            return False

    if settings.REQUIRED_TERMS:
        if not any(term in text for term in settings.REQUIRED_TERMS):
            # Being an internship is the real gate; be lenient here when titles
            # are generic.
            pass

    return True


def text_of(el) -> str:
    """Safe extraction of an element's text, trimmed."""
    if el is None:
        return ""
    return el.get_text(strip=True)
