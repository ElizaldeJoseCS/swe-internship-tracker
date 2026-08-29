# Central configuration for the internship scraper.
#
# Sensitive values (API keys, credentials paths) should live in a .env file,
# loaded via python-dotenv. See .env.example.

import os
from dotenv import load_dotenv

load_dotenv()

# --- Google Sheets -------------------------------------------------------
GSHEET_ID = os.getenv("GSHEET_ID", "")            # The spreadsheet ID from the URL
SHEET_NAME = os.getenv("SHEET_NAME", "Internships")  # Worksheet / tab name
GAME_DEV_SHEET_NAME = os.getenv("GAME_DEV_SHEET_NAME", "Game Dev")  # tab for game roles
NEW_GRAD_SHEET_NAME = os.getenv("NEW_GRAD_SHEET_NAME", "New Grad")  # tab for new-grad roles

# Application status options used for the dropdown + dashboard.
STATUS_OPTIONS = [
    "Not Applied",
    "Interviewing",
    "Not Accepted",
    "Ghosted",
]

CREDENTIALS_FILE = os.getenv(
    "CREDENTIALS_FILE", "config/google_credentials.json"
)
# Scopes only needed to update the sheet with live status. Read-only scraping
# could use a narrower scope, but keeping write enables the dashboard.
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]

# --- Scraping sources (enable/disable) ------------------------------------
SOURCES = {
    "simplify": os.getenv("SCRAPE_SIMPLIFY", "true").lower() == "true",
    "simplify_newgrad": os.getenv("SCRAPE_SIMPLIFY_NEWGRAD", "true").lower() == "true",
    "zapply": os.getenv("SCRAPE_ZAPPLY", "true").lower() == "true",
    "greenhouse": os.getenv("SCRAPE_GREENHOUSE", "true").lower() == "true",
    "lever": os.getenv("SCRAPE_LEVER", "true").lower() == "true",
    "linkedin": os.getenv("SCRAPE_LINKEDIN", "true").lower() == "true",
    "indeed": os.getenv("SCRAPE_INDEED", "true").lower() == "true",
    "gamejobs": os.getenv("SCRAPE_GAMEJOBS", "true").lower() == "true",
}

# --- Search terms ----------------------------------------------------------
# Keywords used to judge whether a posting is relevant (filter).
SEARCH_KEYWORDS = os.getenv(
    "SEARCH_KEYWORDS",
    "software engineer,software engineering,back end,backend,front end,frontend,"
    "full stack,fullstack,devops,data engineer,ml engineer,machine learning,swe,"
    "software developer,intern,internship",
).lower().split(",")

# Required keyword: a posting must contain at least one of these to be kept.
REQUIRED_TERMS = [k.strip() for k in SEARCH_KEYWORDS if k.strip()]

# Optional: list a set of companies you specifically care about. If non-empty,
# only internships from these companies/matching text are kept.
TARGET_COMPANIES = [
    c.strip().lower() for c in os.getenv("TARGET_COMPANIES", "").split(",") if c.strip()
]

# Simplified: target "intern"/"internship" in the title regardless of keyword text.
FILTER_TITLES = (
    os.getenv("FILTER_TITLES", "true").lower() == "true"
)  # only keep jobs whose title suggests an internship

# --- HTTP behavior ---------------------------------------------------------
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "15"))
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# --- Dashboard -------------------------------------------------------------
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "5000"))
DASHBOARD_HOST = os.getenv("DASHBOARD_HOST", "0.0.0.0")

# --- Refresh / dedup -------------------------------------------------------
# How long (seconds) between automatic re-scrapes in the dashboard (0 disables).
AUTO_REFRESH_SECONDS = int(os.getenv("AUTO_REFRESH_SECONDS", "1800"))

# Comma-separated explicit Greenhouse boards. Scraping EVERY greenhouse board is
# impractical; supply the ones for companies you care about.
GREENHOUSE_BOARDS = [
    b.strip()
    for b in os.getenv(
        "GREENHOUSE_BOARDS",
        "",
    ).split(",")
    if b.strip()
]

# Comma-separated explicit Lever boards (e.g. https://jobs.lever.co/companyname)
LEVER_BOARDS = [
    b.strip()
    for b in os.getenv(
        "LEVER_BOARDS",
        "",
    ).split(",")
    if b.strip()
]

# --- GameJobs.co (game-industry job board) ---------------------------------
GAME_MAX_PAGES = int(os.getenv("GAME_MAX_PAGES", "8"))
# If true, keep ALL postings from GameJobs (not just SWE-ish ones).
GAME_KEEP_ALL = os.getenv("GAME_KEEP_ALL", "false").lower() == "true"
