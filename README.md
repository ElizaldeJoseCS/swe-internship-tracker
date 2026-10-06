# Job Alert Tracker

This version no longer uses Google Sheets. It emails only **newly detected**
early-career roles that match:

- Software Engineering: internships + new grad / entry level
- Quant Developer: internships + new grad / entry level, especially C++ / Python
- Game Development: internships + new grad / entry level

It uses the existing Simplify, Zapply, and GameJobs scrapers and remembers
already-emailed application URLs in `data/seen_jobs.json`.

## 1. Gmail setup

Use a Gmail **App Password**, not your normal Gmail password.

1. Turn on 2-Step Verification for the Gmail account you will send from.
2. Create a Google App Password.
3. Put the 16-character App Password into the GitHub repository secret
   `EMAIL_PASSWORD`.

The alert destination is `je2398157@gmail.com`.

## 2. GitHub secrets

Repository -> Settings -> Secrets and variables -> Actions -> New repository secret

Create:

- `ALERT_EMAIL` = `je2398157@gmail.com`
- `SENDER_EMAIL` = the Gmail address sending the email
- `EMAIL_PASSWORD` = Gmail App Password

Do NOT commit the App Password.

## 3. First run

The default is intentionally:

`SEND_EXISTING_ON_FIRST_RUN=false`

So the first scheduled run records jobs that are already open without emailing
you about hundreds of old postings.

After that, when a new posting appears, it is emailed once with its direct
application URL.

If you really want the first run to email every currently-open match, set the
environment variable to `true` for that run.

## 4. Run locally

```bash
pip install -r requirements.txt
python main.py --dry
python main.py --initialize
python main.py
```

`--dry` prints matches without sending email.

`--initialize` records current matches without sending email.

## 5. GitHub Actions

`.github/workflows/job-alerts.yml` runs every 30 minutes and can also be run
manually from the Actions tab.

The workflow commits `data/seen_jobs.json` so the tracker remembers which jobs
have already triggered an alert.

## Matching behavior

A posting must look like an early-career role (intern, co-op, new grad,
entry-level, junior, etc.) and match at least one of the following:

### SWE
Software Engineer, Software Developer, Backend, Frontend, Full Stack,
Systems Engineer, Platform Engineer, DevOps, and similar.

### Quant Developer
Quant Developer, Quantitative Developer, Quantitative Engineer, Trading
Systems, Algorithmic Trading Developer, Trading Software, Research Engineer,
and related quant/trading roles. C++ and Python are explicitly included in
the matching logic.

### Game Development
Gameplay Engineer/Programmer, Game Programmer/Developer, Engine Programmer,
Graphics/Rendering, Game AI, Tools Engineer/Programmer, Unity, Unreal, Game
Server, and related game-engineering roles.

There is deliberately no company whitelist, so the tracker can find roles at
FAANG, major finance firms, game studios, startups, and other companies.
