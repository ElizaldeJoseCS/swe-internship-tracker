# Configuration for the job-alert tracker.
import os
from dotenv import load_dotenv

load_dotenv()

SOURCES = {
    "simplify": os.getenv("SCRAPE_SIMPLIFY", "true").lower() == "true",
    "simplify_newgrad": os.getenv("SCRAPE_SIMPLIFY_NEWGRAD", "true").lower() == "true",
    "zapply": os.getenv("SCRAPE_ZAPPLY", "true").lower() == "true",
    "greenhouse": os.getenv("SCRAPE_GREENHOUSE", "true").lower() == "true",
    "lever": os.getenv("SCRAPE_LEVER", "true").lower() == "true",
    "linkedin": os.getenv("SCRAPE_LINKEDIN", "false").lower() == "true",
    "indeed": os.getenv("SCRAPE_INDEED", "false").lower() == "true",
    "gamejobs": os.getenv("SCRAPE_GAMEJOBS", "true").lower() == "true",
}

# Job-alert matching
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "je2398157@gmail.com")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", ALERT_EMAIL)
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))

# If false, the first run records all currently-open jobs without emailing them.
SEND_EXISTING_ON_FIRST_RUN = (
    os.getenv("SEND_EXISTING_ON_FIRST_RUN", "false").lower() == "true"
)

STATE_FILE = os.getenv("STATE_FILE", "data/seen_jobs.json")
MAX_EMAILS_PER_RUN = int(os.getenv("MAX_EMAILS_PER_RUN", "25"))

# Matching terms. The tracker intentionally does not require a company list:
# it should find SWE, quant-dev, and game-dev roles at essentially any company.
SWE_TERMS = [
    "software engineer", "software engineering", "software developer",
    "swe", "backend", "back end", "frontend", "front end", "full stack",
    "fullstack", "systems engineer", "platform engineer", "infrastructure engineer",
    "devops engineer", "developer infrastructure", "api engineer",
]

QUANT_TERMS = [
    "quant developer", "quantitative developer", "quant dev",
    "quantitative software engineer", "quantitative engineer",
    "quantitative developer intern", "quant developer intern",
    "trading systems", "algorithmic trading developer",
    "trading technology", "trading software", "research engineer",
]

GAME_TERMS = [
    "gameplay programmer", "gameplay engineer", "game programmer",
    "game developer", "game development", "game dev", "gameplay",
    "engine programmer", "engineer - game", "game systems",
    "graphics programmer", "graphics engineer", "rendering engineer",
    "technical programmer", "tools programmer", "tools engineer",
    "game server", "game ai", "game ai engineer", "unity",
    "unreal engine", "video game", "game engine",
]

TECH_TERMS = [
    "c++", "cpp", "python", "unreal", "unity", "godot",
]

# Internship/co-op and entry-level/new-grad markers.
EARLY_CAREER_TERMS = [
    "intern", "internship", "co-op", "coop", "new grad", "new-grad",
    "new graduate", "recent grad", "recent graduate", "entry level",
    "entry-level", "junior", "university graduate", "university grad",
    "2027 start", "2027 new grad", "2028 start", "2028 new grad",
]

REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "20"))
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# These are optional direct ATS boards. Add company slugs here for companies
# you especially want monitored even if an aggregator misses them.
GREENHOUSE_BOARDS = [
    b.strip() for b in os.getenv("GREENHOUSE_BOARDS", "").split(",") if b.strip()
]
LEVER_BOARDS = [
    b.strip() for b in os.getenv("LEVER_BOARDS", "").split(",") if b.strip()
]

GAME_MAX_PAGES = int(os.getenv("GAME_MAX_PAGES", "8"))
GAME_KEEP_ALL = os.getenv("GAME_KEEP_ALL", "false").lower() == "true"

SIMPLIFY_INTERNSHIP_REPO = os.getenv(
    "SIMPLIFY_INTERNSHIP_REPO",
    "https://raw.githubusercontent.com/SimplifyJobs/Summer2027-Internships/dev/README.md",
)
SIMPLIFY_NEWGRAD_REPO = os.getenv(
    "SIMPLIFY_NEWGRAD_REPO",
    "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/README.md",
)
