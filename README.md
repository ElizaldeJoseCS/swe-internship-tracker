# SWE Internship Tracker

Scrapes software-engineering internship and new-grad postings from several
sources into a Google Sheet, where you can track application status
(Not Applied / Interviewing / Not Accepted / Ghosted).

## Features

- **Multi-source scraping**: SimplifyJobs internship + new-grad GitHub repos,
  zapplyjobs new-grad repo, Greenhouse API, Lever API, LinkedIn, Indeed, and a
  game-industry board (GameJobs).
- **Google Sheets** storage with a Status column that survives re-scrapes
  (existing statuses are preserved, rows are refreshed).
- **Three tabs**: roles are split automatically — game-development roles go on
  a "Game Dev" tab, non-game new-grad postings go on a "New Grad" tab, and the
  rest go on the main "Internships" tab.
- **Status dropdown** on the Status column in the sheet for quick updates
  (Not Applied / Interviewing / Not Accepted / Ghosted).
- **Cross-source dedupe**: the same posting found in two repos is only kept once.
- **Skills column**: pulls common tech keywords from each posting so you can see
  what they're looking for at a glance.
- **Safety guard**: won't wipe your sheet if a scrape fails (see below).

## Prerequisites

- **Python 3.9+**
- **Git**
- A **Google Cloud** account to create a service account (free).

## Install (fresh clone)

```bash
git clone <your-repo-url>
cd internships
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Set up Google Sheets access

This lets the scraper write to (and read from) a Google Sheet you own.

1. Go to https://console.cloud.google.com → create a project (or reuse one).
2. Enable the **Google Sheets API**.
3. Go to **IAM & Admin → Service Accounts** → **Create service account**:
   - Name it anything (e.g. `internship-scraper`).
   - After creating, open it → **Keys** → **Add key** → **Create new key** →
     choose **JSON**. Download the key file.
4. Create a blank spreadsheet at https://sheets.new.
   - Click **Share** and add the service account's email (the `client_email`
     field inside the JSON key) as an **Editor**.
5. Save the key file into the repo as `config/google_credentials.json`
   (create the `config/` folder if needed — it isn't committed to git so the
   folder won't exist after cloning):

   ```bash
   mkdir -p config
   cp ~/Downloads/<your-key>.json config/google_credentials.json
   ```

6. Copy the spreadsheet ID from its URL. In
   `https://docs.google.com/spreadsheets/d/<GSHEET_ID>/edit`, take the
   `<GSHEET_ID>` part (the `1k...` string).

> The credentials file and `.env` are both git-ignored, so your key and sheet ID
> never get committed.

## Configure

```bash
cp .env.example .env
# edit .env and set at least:
#   GSHEET_ID=<your spreadsheet id or full url>
#   GREENHOUSE_BOARDS=<comma-separated slugs>   (if using Greenhouse)
#   LEVER_BOARDS=<comma-separated slugs>        (if using Lever)
```

Every `.env` option is documented in `.env.example`. The most important ones:

| Variable | Purpose | Default |
|----------|---------|---------|
| `GSHEET_ID` | Your spreadsheet ID (or full URL). **Required.** | — |
| `CREDENTIALS_FILE` | Path to your service-account key. | `config/google_credentials.json` |
| `SHEET_NAME` | Main tab name. | `Internships` |
| `NEW_GRAD_SHEET_NAME` | Tab for new-grad roles. | `New Grad` |
| `GAME_DEV_SHEET_NAME` | Tab for game-industry roles. | `Game Dev` |
| `SCRAPE_*` | Toggle each source on/off. | GitHub + API sources on; LinkedIn/Indeed off |
| `GREENHOUSE_BOARDS` | Comma-separated board slugs (e.g. `stripe,airbnb`). | empty |
| `LEVER_BOARDS` | Comma-separated board slugs (e.g. `palantir,rover`). | empty |
| `TARGET_COMPANIES` | If set, keep only these companies. | empty |
| `GAME_MAX_PAGES` | GameJobs feed pages to scrape. | `8` |

## Run

```bash
python main.py            # writes to your sheet
python main.py --dry      # just prints, doesn't touch the sheet
python main.py --force    # write even if the scrape looks too small
```

**Safety guard**: if a scrape (e.g. after a transient network error on GitHub)
yields far fewer rows than already in the sheet, the script stops and leaves
your existing rows untouched instead of overwriting them. If you *really* want
to replace everything, pass `--force`.

Statuses are edited directly in the Google Sheet's **Status** column via the
dropdown — no code needed. Their changes survive every re-scrape.

## Project layout

```
internships/
├── main.py             # CLI scraper -> Google Sheets
├── models.py           # Internship dataclass + dedupe
├── game_dev.py         # game-dev role classifier (separate tab)
├── new_grad.py         # new-grad vs internship classifier (separate tab)
├── sheets_manager.py   # Google Sheets read/write
├── config/settings.py  # central configuration (reads .env)
├── scrapers/
│   ├── common.py       # HTTP session + relevance filtering
│   ├── simplify.py     # SimplifyJobs internship + new-grad GitHub repos
│   ├── zapply.py       # zapplyjobs New-Grad-Jobs-2027 GitHub repo
│   ├── greenhouse.py   # Greenhouse boards API
│   ├── lever.py        # Lever postings API
│   ├── linkedin.py     # LinkedIn guest search
│   ├── indeed.py       # Indeed search
│   ├── gamejobs.py     # GameJobs.co game-industry board
│   └── __init__.py     # orchestrator
```

## Configuring sources

| Source | How to enable | Notes |
|--------|---------------|-------|
| **Simplify (intern)** | `SCRAPE_SIMPLIFY=true` | Community internships GitHub repo. |
| **Simplify (new grad)** | `SCRAPE_SIMPLIFY_NEWGRAD=true` | Community new-grad GitHub repo. |
| **zapplyjobs** | `SCRAPE_ZAPPLY=true` | New-Grad-Jobs-2027 GitHub repo (kept to SWE roles). |
| **Greenhouse** | `SCRAPE_GREENHOUSE=true` + `GREENHOUSE_BOARDS=stripe,airbnb` | Uses the public boards API. Set the board slugs you care about. |
| **Lever** | `SCRAPE_LEVER=true` + `LEVER_BOARDS=acme,foo` | Uses the public postings API. |
| **LinkedIn** | `SCRAPE_LINKEDIN=true` (+ optionally `LINKEDIN_COOKIE`) | Guest scraping; may be rate-limited/blocked. A session cookie helps. |
| **Indeed** | `SCRAPE_INDEED=true` | Same anti-bot caveats as LinkedIn. |
| **GameJobs** | `SCRAPE_GAMEJOBS=true` | Game-industry job board. |

Legal note: job sites' ToS often prohibit scraping; use reasonable rate limits
and consider the API-based sources (Greenhouse/Lever/Simplify) as your primary
reliable sources. Keep personal requests low and respect robots.txt.

## Application statuses (Status dropdown)

- **Not Applied** — default for new rows
- **Interviewing** — you have an interview/process in progress
- **Not Accepted** — the company passed on your application
- **Ghosted** — applied but never heard back
