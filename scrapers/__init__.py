# Orchestrator: run all enabled scrapers and merge/dedupe the results.

from models import Internship, dedupe
from config import settings

from scrapers import (
    simplify,
    zapply,
    greenhouse,
    lever,
    linkedin,
    indeed,
    gamejobs,
)


def _enabled() -> list[str]:
    return [name for name, on in settings.SOURCES.items() if on]


def run_all() -> list[Internship]:
    enabled = _enabled()
    if not enabled:
        print("No sources enabled. Set SCRAPE_* in your .env / settings.")
        return []

    print(f"Running scrapers: {', '.join(enabled)}")
    all_items: list[Internship] = []

    if "simplify" in enabled:
        try:
            all_items.extend(simplify.scrape_internships())
        except Exception as e:
            print(f"  ! simplify scraper error: {e}")

    if "simplify_newgrad" in enabled:
        try:
            all_items.extend(simplify.scrape_newgrad())
        except Exception as e:
            print(f"  ! simplify new-grad scraper error: {e}")

    if "zapply" in enabled:
        try:
            all_items.extend(zapply.scrape())
        except Exception as e:
            print(f"  ! zapply scraper error: {e}")

    if "greenhouse" in enabled:
        try:
            all_items.extend(greenhouse.scrape())
        except Exception as e:
            print(f"  ! greenhouse scraper error: {e}")

    if "lever" in enabled:
        try:
            all_items.extend(lever.scrape())
        except Exception as e:
            print(f"  ! lever scraper error: {e}")

    if "linkedin" in enabled:
        try:
            all_items.extend(linkedin.scrape())
        except Exception as e:
            print(f"  ! linkedin scraper error: {e}")

    if "indeed" in enabled:
        try:
            all_items.extend(indeed.scrape())
        except Exception as e:
            print(f"  ! indeed scraper error: {e}")

    if "gamejobs" in enabled:
        try:
            all_items.extend(gamejobs.scrape())
        except Exception as e:
            print(f"  ! gamejobs scraper error: {e}")

    merged = dedupe(all_items)
    print(f"Total merged (after dedupe): {len(merged)}")
    return merged
