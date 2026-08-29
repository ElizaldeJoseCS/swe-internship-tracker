# Google Sheets integration: write scraped internships, read/update status.
#
# Two authentication modes:
#   1. Service account (recommended): create one in Google Cloud, share the
#      spreadsheet with the service-account email as Editor. Store the JSON
#      key at config/google_credentials.json
#   2. OAuth user flow: paste a client secret and complete the one-time local
#      consent to produce a token. (Not implemented here by default.)

import os
import re
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import settings

# Column order in the sheet.
HEADERS = [
    "Company",
    "Title",
    "Location",
    "Link",
    "Source",
    "Skills",
    "Posted Date",
    "Status",
    "Notes",
    "Scraped At",
]

STATUS_COLUMN = HEADERS.index("Status")  # 0-based

# Every worksheet/tab the manager reads/writes.
_ALL_TABS = (settings.SHEET_NAME, settings.GAME_DEV_SHEET_NAME, settings.NEW_GRAD_SHEET_NAME)


def _sheet_id() -> str:
    """Return a bare spreadsheet ID, extracting it from a full URL if needed."""
    raw = settings.GSHEET_ID.strip()
    m = re.search(r"/d/([a-zA-Z0-9-_]+)", raw)
    if m:
        return m.group(1)
    return raw


def _credentials():
    if not os.path.exists(settings.CREDENTIALS_FILE):
        raise FileNotFoundError(
            f"Credentials file not found: {settings.CREDENTIALS_FILE}\n"
            "See README for how to create a service account and download the JSON."
        )
    return service_account.Credentials.from_service_account_file(
        settings.CREDENTIALS_FILE, scopes=settings.GOOGLE_SCOPES
    )


def _service():
    return build("sheets", "v4", credentials=_credentials())


def _range_name(sheet_name: str = None) -> str:
    return f"{sheet_name or settings.SHEET_NAME}!A:J"


def _add_status_dropdown(service, sheet_name: str):
    """Add a Google Sheets data-validation dropdown to the Status column."""
    n_rows = _max_rows(service, sheet_name)
    if n_rows < 2:
        n_rows = 1000  # apply to a generous range so new rows get the dropdown
    col = chr(ord("A") + STATUS_COLUMN)
    body = {
        "requests": [
            {
                "setDataValidation": {
                    "range": {
                        "sheetId": _sheet_id_by_name(service, sheet_name),
                        "startRowIndex": 1,
                        "endRowIndex": n_rows,
                        "startColumnIndex": STATUS_COLUMN,
                        "endColumnIndex": STATUS_COLUMN + 1,
                    },
                    "rule": {
                        "condition": {
                            "type": "ONE_OF_LIST",
                            "values": [{"userEnteredValue": o} for o in settings.STATUS_OPTIONS],
                        },
                        "strict": True,
                        "showCustomUi": True,
                    },
                }
            }
        ]
    }
    try:
        service.spreadsheets().batchUpdate(
            spreadsheetId=_sheet_id(), body=body
        ).execute()
    except HttpError as e:
        print(f"  sheets: could not add status dropdown: {e}")


def _sheet_id_by_name(service, sheet_name: str) -> int:
    meta = (
        service.spreadsheets().get(spreadsheetId=_sheet_id()).execute()
    )
    for sheet in meta.get("sheets", []):
        if sheet["properties"]["title"] == sheet_name:
            return sheet["properties"]["sheetId"]
    return 0


def _max_rows(service, sheet_name: str) -> int:
    meta = service.spreadsheets().get(spreadsheetId=_sheet_id()).execute()
    for sheet in meta.get("sheets", []):
        if sheet["properties"]["title"] == sheet_name:
            return sheet["properties"]["gridProperties"].get("rowCount", 1000)
    return 1000


def _ensure_headers(service, sheet_name: str = None):
    """Create the worksheet/header row if missing, otherwise no-op."""
    sheet_name = sheet_name or settings.SHEET_NAME
    sheet = service.spreadsheets().values()
    rng = f"{sheet_name}!A:J"
    try:
        sheet.get(spreadsheetId=_sheet_id(), range=rng).execute()
        return
    except HttpError as e:
        if e.resp.status in (400, 404):
            pass  # worksheet probably missing; we'll create below
        else:
            raise

    # Create worksheet if the API says the sheet is missing.
    try:
        body = {
            "requests": [
                {
                    "addSheet": {
                        "properties": {
                            "title": sheet_name,
                            "gridProperties": {"rowCount": 2, "columnCount": 10},
                        }
                    }
                }
            ]
        }
        service.spreadsheets().batchUpdate(
            spreadsheetId=_sheet_id(), body=body
        ).execute()
    except HttpError as e:
        print(f"  sheets: could not auto-create worksheet: {e}")

    # Write header row.
    sheet.update(
        spreadsheetId=_sheet_id(),
        range=f"{sheet_name}!A1:J1",
        valueInputOption="RAW",
        body={"values": [HEADERS]},
    ).execute()


def write_internships(items, status_map: Optional[dict] = None):
    """Replace the sheet contents with the given internships.

    Splits roles into three tabs: game-dev roles go to the 'Game Dev' tab, and
    of the remaining roles, new-grad postings go to the 'New Grad' tab while the
    rest go to the main 'Internships' tab. Existing statuses are preserved
    across re-scrapes, and a Status dropdown is (re)applied to all tabs.
    """
    from game_dev import is_game_dev
    from new_grad import is_new_grad

    service = _service()
    _ensure_headers(service, settings.SHEET_NAME)
    _ensure_headers(service, settings.GAME_DEV_SHEET_NAME)
    _ensure_headers(service, settings.NEW_GRAD_SHEET_NAME)

    if status_map is None:
        status_map = read_statuses()

    game_items = [i for i in items if is_game_dev(i)]
    non_game = [i for i in items if not is_game_dev(i)]
    newgrad_items = [i for i in non_game if is_new_grad(i)]
    reg_items = [i for i in non_game if not is_new_grad(i)]

    _write_tab(service, settings.SHEET_NAME, reg_items, status_map)
    _write_tab(service, settings.GAME_DEV_SHEET_NAME, game_items, status_map)
    _write_tab(service, settings.NEW_GRAD_SHEET_NAME, newgrad_items, status_map)
    _add_status_dropdown(service, settings.SHEET_NAME)
    _add_status_dropdown(service, settings.GAME_DEV_SHEET_NAME)
    _add_status_dropdown(service, settings.NEW_GRAD_SHEET_NAME)
    print(
        f"  sheets: wrote {len(reg_items)} rows to {settings.SHEET_NAME}, "
        f"{len(newgrad_items)} rows to {settings.NEW_GRAD_SHEET_NAME}, "
        f"and {len(game_items)} rows to {settings.GAME_DEV_SHEET_NAME}"
    )


def _write_tab(service, sheet_name: str, items, status_map: dict):
    sheet = service.spreadsheets().values()
    rows = [_row_for(item, status_map) for item in items]
    values = [HEADERS] + rows
    try:
        sheet.batchClear(
            spreadsheetId=_sheet_id(),
            body={"ranges": [f"{sheet_name}!A2:J"]},
        ).execute()
    except HttpError:
        pass
    sheet.update(
        spreadsheetId=_sheet_id(),
        range=f"{sheet_name}!A1",
        valueInputOption="RAW",
        body={"values": values},
    ).execute()


def _norm_date(value) -> str:
    """Return a clean YYYY-MM-DD for a posted_date value from any source."""
    if not value:
        return ""
    value = str(value).strip()
    # value[:10] works for ISO values like '2026-08-28T03:10:32+00:00'.
    m = re.match(r"(\d{4}-\d{2}-\d{2})", value)
    return m.group(1) if m else value[:10]


def _row_for(item, status_map: dict) -> list:
    got = status_map.get(item.url.strip().lower(), item.status)
    return [
        item.company,
        item.title,
        item.location,
        item.url,
        item.source,
        item.skills,
        _norm_date(item.posted_date),
        got,
        "",
        getattr(item, "scraped_at", "") or "",
    ]


def read_statuses() -> dict:
    """Return {url_lower: status} for all rows across every tab (Internships,
    Game Dev, New Grad)."""
    result = {}
    service = _service()
    sheet = service.spreadsheets().values()
    for tab in _ALL_TABS:
        try:
            resp = (
                sheet.get(spreadsheetId=_sheet_id(), range=f"{tab}!A:J")
                .execute()
                .get("values", [])
            )
        except HttpError as e:
            # Worksheet/tab missing on first run is expected — just no statuses yet.
            if e.resp.status in (400, 404):
                continue
            print(f"  sheets: could not read current statuses: {e}")
            continue
        except Exception as e:
            print(f"  sheets: could not read current statuses: {e}")
            continue

        if len(resp) < 2:
            continue
        for row in resp[1:]:
            if len(row) >= 4 and len(row) > STATUS_COLUMN:
                url = row[3].strip().lower()
                if url:
                    result[url] = row[STATUS_COLUMN]
    return result


def update_status(url: str, new_status: str) -> bool:
    """Update the Status cell for the row whose Link column matches `url`."""
    service = _service()
    sheet = service.spreadsheets().values()
    target = url.strip().lower()
    for tab in _ALL_TABS:
        current = _load_all_rows(sheet, tab)
        for row_num, row in enumerate(current, start=1):
            link = row[3].strip().lower() if len(row) > 3 else ""
            if link == target:
                col = chr(ord("A") + STATUS_COLUMN)
                cell = f"{tab}!{col}{row_num}"
                sheet.update(
                    spreadsheetId=_sheet_id(),
                    range=cell,
                    valueInputOption="RAW",
                    body={"values": [[new_status]]},
                ).execute()
                return True
    return False


def _load_all_rows(sheet, sheet_name: str = None) -> list:
    sheet_name = sheet_name or settings.SHEET_NAME
    try:
        resp = (
            sheet.get(spreadsheetId=_sheet_id(), range=f"{sheet_name}!A:J")
            .execute()
            .get("values", [])
        )
    except HttpError as e:
        if e.resp.status in (400, 404):
            return []
        raise
    return resp


def load_all() -> list[dict]:
    """Return all rows from every tab keyed by header (for the dashboard)."""
    service = _service()
    sheet = service.spreadsheets().values()
    out = []
    for tab in _ALL_TABS:
        resp = _load_all_rows(sheet, tab)
        if not resp:
            continue
        headers = resp[0]
        for row in resp[1:]:
            row = (row + [""] * (len(headers) - len(row)))[: len(headers)]
            out.append(dict(zip(headers, row)))
    return out


def count_rows() -> int:
    """Return the total number of data rows (excluding headers) across all tabs.

    Used as the source-of-truth baseline for the main.py safety guard so a
    failed/partial scrape doesn't wipe existing rows.
    """
    service = _service()
    sheet = service.spreadsheets().values()
    total = 0
    for tab in _ALL_TABS:
        resp = _load_all_rows(sheet, tab)
        # Drop blank trailing rows and the header row; count the rest.
        for row in resp[1:]:
            if any((c or "").strip() for c in row):
                total += 1
    return total
