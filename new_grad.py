# New-grad role classifier.
# Determines whether a (non-game-dev) posting belongs on the "New Grad" tab
# rather than the "Internships" tab.
#
# Heuristic: a role is new-grad if its title (and to a lesser extent skills)
# explicitly mentions new-grad / recent-graduate / entry-level markers. Pure
# internships ("intern", "internship", "co-op", "apprentice") are left on the
# Internships tab.

import re

# Title markers (word-boundary anchored where it matters) for new-grad roles.
_NEW_GRAD_PATTERNS = [
    r"\bnew\s*-?\s*grad",       # new grad, new-grad
    r"\bnew\s+graduate",        # new graduate
    r"\brecent\s+grad",         # recent grad
    r"\brecent\s+graduate",     # recent graduate
    r"\bgrad\b",                # "grad" shorthand
    r"\bgraduate\b",            # graduate / (no intern word)
    r"\bentry[- ]level\b",      # entry-level / entry level
    r"\bjunior\b",              # junior software engineer
    r"\buniversity\s+grad",     # university grad
]

# Year tokens that signal a new-grad cohort (e.g. "2027 Start", "Class of 2026").
_YEAR_RE = re.compile(r"\b(20\d\d)\b")

# If the title is clearly an internship, it should never be classified new-grad,
# even if a stray marker sneaks in.
_INTERN_PATTERNS = [
    r"\bintern\b",
    r"\binternship\b",
    r"\bco-?op\b",
    r"\bapprentice\b",
]


def is_new_grad(item) -> bool:
    """Return True if a non-game role should go on the 'New Grad' tab."""
    if not item:
        return False

    title = (getattr(item, "title", "") or "").lower()
    if any(re.search(p, title) for p in _INTERN_PATTERNS):
        return False

    if any(re.search(p, title) for p in _NEW_GRAD_PATTERNS):
        return True

    # A bare year in the title (e.g. "Software Engineer - 2027") usually denotes
    # a new-grad/intake cohort for that start year, not an internship.
    if _YEAR_RE.search(title):
        return True

    return False
