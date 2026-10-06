"""Match scraped postings to the user's alert categories."""

import re
from config import settings

def _text(item):
    return " ".join([
        getattr(item, "company", "") or "",
        getattr(item, "title", "") or "",
        getattr(item, "skills", "") or "",
        getattr(item, "source", "") or "",
    ]).lower()

def _has_any(text, terms):
    return any(term.lower() in text for term in terms)

def is_early_career(item):
    title = (getattr(item, "title", "") or "").lower()
    return _has_any(title, settings.EARLY_CAREER_TERMS)

def is_swe(item):
    return _has_any(_text(item), settings.SWE_TERMS)

def is_quant(item):
    text = _text(item)
    # Quant dev should be explicitly quant/trading/financial-engineering related.
    if _has_any(text, settings.QUANT_TERMS):
        return True
    return bool(
        re.search(r"\bquant\b|\bquantitative\b|\btrading\b", text)
        and _has_any(text, settings.TECH_TERMS)
    )

def is_game(item):
    text = _text(item)
    source = (getattr(item, "source", "") or "").lower()
    if source == "gamejobs":
        return True
    return _has_any(text, settings.GAME_TERMS)

def categories(item):
    out = []
    if is_quant(item):
        out.append("Quant Developer")
    if is_game(item):
        out.append("Game Development")
    if is_swe(item) and not is_quant(item):
        out.append("Software Engineering")
    return out

def is_match(item):
    """Only alert on early-career SWE, quant-dev, or game-dev roles."""
    if not getattr(item, "url", ""):
        return False
    if not is_early_career(item):
        return False
    return bool(categories(item))
