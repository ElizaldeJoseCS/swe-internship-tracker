"""Persistent state for jobs that have already triggered an email."""

import json
import os
from config import settings

def load_seen():
    path = settings.STATE_FILE
    if not os.path.exists(path):
        return set(), False

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("urls", [])), True
    except (OSError, ValueError, TypeError):
        return set(), False

def save_seen(urls):
    path = settings.STATE_FILE
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {"urls": sorted(urls)},
            f,
            indent=2,
        )

def normalize_url(url):
    return (url or "").strip().lower().split("?", 1)[0].split("#", 1)[0].rstrip("/")
