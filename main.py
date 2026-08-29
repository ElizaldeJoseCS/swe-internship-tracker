# CLI entry point: run the scrapers and write results to Google Sheets.
#
# Usage examples:
#   python main.py              # run all enabled sources, write to the sheet
#   python main.py --dry        # print results to stdout, don't touch sheet
#   python main.py --json out   # write results to out/ as JSON too

import argparse
import json
import os
from datetime import datetime

from scrapers import run_all
import sheets_manager


def _slice_marker() -> str:
    """Return a short machine-readable marker for run outputs."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def main():
    parser = argparse.ArgumentParser(description="Scrape SWE internships to Google Sheets")
    parser.add_argument("--dry", action="store_true", help="Don't write to the sheet, just print.")
    parser.add_argument("--json", metavar="DIR", help="Also dump results as JSON into DIR.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Write even if the scrape looks too small (skips the safety guard).",
    )
    args = parser.parse_args()

    internships = run_all()

    if args.json:
        os.makedirs(args.json, exist_ok=True)
        path = os.path.join(
            args.json, f"internships_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(path, "w", encoding="utf-8") as f:
            json.dump([i.to_dict() for i in internships], f, indent=2, default=str)
        print(f"Wrote JSON -> {path}")

    if args.dry:
        for i in internships:
            print(f"  [{i.source}] {i.company}: {i.title} | {i.location} | {i.url}")
        print(f"\n{len(internships)} total (dry run, sheet not modified).")
        return

    if not internships:
        print("Nothing scraped; sheet not modified.")
        return

    # Safety guard: if the new scrape has far fewer rows than what's already in
    # the sheet, one or more sources likely failed (e.g. a network error) and
    # overwriting would wipe existing rows. Abort unless --force is passed.
    existing = sheets_manager.count_rows()
    threshold = 0.5  # require the new scrape to be at least 50% of existing rows
    if (
        not args.force
        and existing > 20
        and len(internships) < int(existing * threshold)
    ):
        print(
            f"  ! Safety guard triggered: scraped {len(internships)} rows but the "
            f"sheet already has {existing}. A source likely failed, so the sheet "
            f"was NOT modified. Re-run to retry, or use --force to overwrite anyway."
        )
        return

    # Preserve statuses from the previous scrape.
    status_map = sheets_manager.read_statuses()
    sheets_manager.write_internships(internships, status_map=status_map)
    print("Done. Open your Google Sheet to view results.")


if __name__ == "__main__":
    main()
