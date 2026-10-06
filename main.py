"""Run the job scrapers and email only newly detected matching roles."""

import argparse
import os
from datetime import datetime

from scrapers import run_all
from job_filter import is_match, categories
from email_notifier import send_job_alert
from alert_state import load_seen, save_seen, normalize_url
from config import settings

def main():
    parser = argparse.ArgumentParser(
        description="Find early-career SWE, quant-dev, and game-dev jobs and email new matches."
    )
    parser.add_argument(
        "--dry",
        action="store_true",
        help="Print matching jobs without sending email or changing state.",
    )
    parser.add_argument(
        "--initialize",
        action="store_true",
        help="Record all currently visible matching jobs without emailing them.",
    )
    args = parser.parse_args()

    jobs = run_all()
    matches = [job for job in jobs if is_match(job)]

    # Deduplicate by normalized URL.
    unique = {}
    for job in matches:
        key = normalize_url(job.url)
        if key:
            unique[key] = job
    matches = list(unique.values())

    print(f"Scraped: {len(jobs)} jobs")
    print(f"Matching early-career alerts: {len(matches)}")

    seen, has_state = load_seen()

    if args.dry:
        for job in matches:
            print(
                f"[{', '.join(categories(job))}] "
                f"{job.company} | {job.title} | {job.location} | {job.url}"
            )
        return

    # First run is a bootstrap by default. This prevents a flood of emails
    # for every job that was already open before the tracker was installed.
    if args.initialize or (not has_state and not settings.SEND_EXISTING_ON_FIRST_RUN):
        for job in matches:
            seen.add(normalize_url(job.url))
        save_seen(seen)
        print(
            f"Initialized state with {len(matches)} currently-open matching jobs. "
            "No emails sent."
        )
        return

    new_jobs = [
        job for job in matches
        if normalize_url(job.url) not in seen
    ]

    # Oldest first is nicer if several jobs appeared between scheduled runs.
    new_jobs.sort(key=lambda j: (j.posted_date or "9999-99-99", j.company, j.title))

    print(f"New jobs requiring email: {len(new_jobs)}")

    sent = 0
    for job in new_jobs[: settings.MAX_EMAILS_PER_RUN]:
        try:
            send_job_alert(job, categories(job))
            seen.add(normalize_url(job.url))
            sent += 1
            print(f"  emailed: {job.company} — {job.title}")
        except Exception as exc:
            # Do NOT mark a failed email as seen, so the next run retries it.
            print(f"  email failed for {job.company} — {job.title}: {exc}")

    # Also remember jobs we didn't email only if they were already known.
    # New jobs beyond MAX_EMAILS_PER_RUN stay un-seen and will be emailed next run.
    save_seen(seen)

    print(f"Sent {sent} alert(s). State contains {len(seen)} jobs.")

if __name__ == "__main__":
    main()
