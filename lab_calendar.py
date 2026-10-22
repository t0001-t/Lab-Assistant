"""Local lab calendar with iCalendar import/export and subscription sync.

The module is deliberately dependency-free. Events and calendar accounts live in
their own SQLite database next to the notebook, so the calendar can be backed up
together with the notebook folder. Subscription sync fetches published ``.ics``
feeds (Google Calendar, Apple/iCloud, Outlook and generic CalDAV servers all
offer such a URL); no OAuth credentials are stored.
"""

from __future__ import annotations

import calendar as month_calendar
import hashlib
import re
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

EVENT_KINDS = ("practicum", "deadline", "incubation", "submission", "todo", "other")
IMPORTANCE_LEVELS = ("low", "normal", "high")
ACCOUNT_PROVIDERS = ("ical", "caldav", "google", "apple", "outlook")
MAX_FEED_BYTES = 2 * 1024 * 1024
_FEED_TIMEOUT = 15


def now() -> str:
    """UTC timestamp with second precision for audit fields."""
    return datetime.now(UTC).isoformat(timespec="seconds")


def _escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace(";", "\\;")
        .replace(",", "\\,")
    )


def _unescape(value: str) -> str:
    escapes = {"n": "\n", "N": "\n", "\\": "\\", ",": ",", ";": ";"}
    return re.sub(r"\\(.)", lambda match: escapes.get(match.group(1), match.group(0)), value)


def _parse_date(raw: str) -> tuple[str, str]:
    """Return ``(YYYY-MM-DD, HH:MM)`` from an iCalendar date or datetime value."""
    value = raw.strip().removesuffix("Z")
    match = re.fullmatch(r"(\d{8})(?:T(\d{6}))?", value)
    if not match:
        raise ValueError("Unsupported iCalendar date")
    day = datetime.strptime(match.group(1), "%Y%m%d").date()
    clock = ""
    if match.group(2):
        clock = f"{match.group(2)[:2]}:{match.group(2)[2:4]}"
    return day.isoformat(), clock


def _unfold(text: str) -> list[str]:
    return re.sub(r"\r?\n[ \t]", "", text).splitlines()


def parse_ics(text: str) -> list[dict]:
    """Parse VEVENT records from an iCalendar document.

    Unknown properties are ignored. Recurring events are imported once with
    their first occurrence; the local calendar intentionally stays simple.
    """
    if "BEGIN:VCALENDAR" not in text.upper():
        raise ValueError("Not an iCalendar document")
    events: list[dict] = []
    current: dict[str, str] | None = None
    for line in _unfold(text):
        stripped = line.strip()
        upper = stripped.upper()
        if upper == "BEGIN:VEVENT":
            current = {}
            continue
        if upper == "END:VEVENT":
            if current is not None:
                event = _event_from_properties(current)
                if event is not None:
                    events.append(event)
            current = None
            continue
        if current is None or ":" not in stripped:
            continue
        name, value = stripped.split(":", 1)
        key = name.split(";", 1)[0].upper()
        current[key] = value
    return events


def _event_from_properties(properties: dict[str, str]) -> dict | None:
    raw_start = properties.get("DTSTART", "").strip()
    if not raw_start:
        return None
    try:
        day, clock = _parse_date(raw_start)
    except ValueError:
        return None
    title = _unescape(properties.get("SUMMARY", "").strip()) or day
    notes = _unescape(properties.get("DESCRIPTION", "").strip())
    uid = properties.get("UID", "").strip()
    if not uid:
        uid = hashlib.sha1(f"{title}|{day}|{clock}".encode()).hexdigest()[:24]
    end_day = end_clock = ""
    if properties.get("DTEND"):
        try:
            end_day, end_clock = _parse_date(properties["DTEND"])
        except ValueError:
            pass
    importance = "normal"
    try:
        priority = int(properties.get("PRIORITY", "").strip())
    except ValueError:
        priority = 5
    if priority <= 4:
        importance = "high"
    elif priority >= 6:
        importance = "low"
    return {
        "uid": uid,
        "title": title,
        "date": day,
        "time": clock,
        "end_date": end_day,
        "end_time": end_clock,
        "notes": notes,
        "importance": importance,
    }


def fetch_ics(url: str) -> str:
    """Fetch a published iCalendar feed with a strict size and scheme limit."""
    parsed = urllib.parse.urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Calendar URL must be an http(s) address")
    request = urllib.request.Request(
        url, headers={"User-Agent": "LabAssistant/1.0 (calendar sync)"}
    )
    try:
        with urllib.request.urlopen(request, timeout=_FEED_TIMEOUT) as response:
            data = response.read(MAX_FEED_BYTES + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise ValueError("Calendar feed could not be loaded") from error
    if len(data) > MAX_FEED_BYTES:
        raise ValueError("Calendar feed is too large")
    return data.decode("utf-8", errors="replace")


def month_matrix(year: int, month: int, events: list[dict]) -> list[list[dict]]:
    """Return Monday-first calendar weeks with the events attached to each day."""
    grouped: dict[str, list[dict]] = {}
    for event in events:
        grouped.setdefault(event["date"], []).append(event)
    for day_events in grouped.values():
        day_events.sort(key=lambda item: (item.get("time", ""), item.get("title", "")))
    weeks = month_calendar.Calendar(firstweekday=0).monthdatescalendar(year, month)
    return [
        [
            {
                "date": day,
                "in_month": day.month == month,
                "events": grouped.get(day.isoformat(), []),
            }
            for day in week
        ]
        for week in weeks
    ]


def shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    index = year * 12 + (month - 1) + delta
    return index // 12, index % 12 + 1


class CalendarStore:
    """SQLite repository for events and calendar subscriptions."""

    def __init__(self, folder: Path | str):
        self.folder = Path(folder).expanduser().resolve()
        self.folder.mkdir(parents=True, exist_ok=True)
        self.db = self.folder / "lab_calendar.sqlite3"
        self._init_schema()

    @contextmanager
    def session(self) -> Iterator[sqlite3.Connection]:
        con = sqlite3.connect(self.db)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA busy_timeout=5000")
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def _init_schema(self) -> None:
        with self.session() as con:
            con.execute("PRAGMA journal_mode=WAL")
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS events (
                  id TEXT PRIMARY KEY,
                  title TEXT NOT NULL,
                  date TEXT NOT NULL,
                  time TEXT NOT NULL DEFAULT '',
                  kind TEXT NOT NULL DEFAULT 'other',
                  importance TEXT NOT NULL DEFAULT 'normal',
                  notes TEXT NOT NULL DEFAULT '',
                  uid TEXT NOT NULL DEFAULT '',
                  source TEXT NOT NULL DEFAULT 'manual',
                  created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS events_date ON events(date, time);
                CREATE INDEX IF NOT EXISTS events_uid ON events(uid, source);
                CREATE TABLE IF NOT EXISTS accounts (
                  id TEXT PRIMARY KEY,
                  provider TEXT NOT NULL,
                  label TEXT NOT NULL,
                  url TEXT NOT NULL,
                  last_sync TEXT NOT NULL DEFAULT '',
                  status TEXT NOT NULL DEFAULT '',
                  created_at TEXT NOT NULL
                );
                """
            )
            columns = {
                row["name"] for row in con.execute("PRAGMA table_info(events)")
            }
            if "importance" not in columns:
                # Existing calendars stay readable and get a neutral default.
                con.execute(
                    "ALTER TABLE events ADD COLUMN importance TEXT NOT NULL DEFAULT 'normal'"
                )

    @staticmethod
    def _rows(cursor: sqlite3.Cursor) -> list[dict]:
        return [dict(row) for row in cursor.fetchall()]

    def list_events(self, start: str | None = None, end: str | None = None) -> list[dict]:
        query = "SELECT * FROM events"
        parameters: list[str] = []
        if start and end:
            query += " WHERE date BETWEEN ? AND ?"
            parameters.extend((start, end))
        elif start:
            query += " WHERE date >= ?"
            parameters.append(start)
        elif end:
            query += " WHERE date <= ?"
            parameters.append(end)
        query += " ORDER BY date, CASE WHEN time='' THEN '00:00' ELSE time END, title"
        with self.session() as con:
            return self._rows(con.execute(query, parameters))

    def get_event(self, event_id: str) -> dict | None:
        with self.session() as con:
            row = con.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
        return dict(row) if row else None

    def add_event(self, title: str, date: str, time: str = "", kind: str = "other",
                  notes: str = "", uid: str = "", source: str = "manual",
                  importance: str = "normal") -> str:
        title = title.strip()
        if not title:
            raise ValueError("Event title is required")
        self._validate(date, time, kind, importance)
        identifier = str(uuid.uuid4())
        with self.session() as con:
            con.execute(
                """INSERT INTO events
                   (id,title,date,time,kind,importance,notes,uid,source,created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (identifier, title, date, time, kind, importance,
                 notes.strip(), uid, source, now()),
            )
        return identifier

    def update_event(self, event_id: str, *, title: str, date: str, time: str = "",
                     kind: str = "other", notes: str = "",
                     importance: str = "normal") -> None:
        title = title.strip()
        if not title:
            raise ValueError("Event title is required")
        self._validate(date, time, kind, importance)
        with self.session() as con:
            cursor = con.execute(
                """UPDATE events SET title=?, date=?, time=?, kind=?, importance=?,
                                    notes=? WHERE id=?""",
                (title, date, time, kind, importance, notes.strip(), event_id),
            )
            if cursor.rowcount == 0:
                raise KeyError(event_id)

    @staticmethod
    def _validate(date_value: str, time_value: str, kind: str,
                  importance: str = "normal") -> None:
        datetime.strptime(date_value, "%Y-%m-%d")
        if time_value:
            if not re.fullmatch(r"[0-2][0-9]:[0-5][0-9]", time_value):
                raise ValueError("Time must use HH:MM")
            datetime.strptime(time_value, "%H:%M")
        if kind not in EVENT_KINDS:
            raise ValueError("Unsupported event kind")
        if importance not in IMPORTANCE_LEVELS:
            raise ValueError("Unsupported importance")

    def delete_event(self, event_id: str) -> None:
        with self.session() as con:
            con.execute("DELETE FROM events WHERE id=?", (event_id,))

    def events_on(self, day: str) -> list[dict]:
        return self.list_events(day, day)

    def upsert_todo_event(self, todo_id: str, title: str, due_date: str,
                          notes: str = "") -> None:
        """Create or move the calendar entry linked to a dated to-do."""
        if not due_date:
            self.delete_todo_event(todo_id)
            return
        title = title.strip()
        if not title:
            raise ValueError("To-do title is required")
        self._validate(due_date, "", "todo", "normal")
        with self.session() as con:
            row = con.execute(
                "SELECT id FROM events WHERE uid=? AND source='todo'", (todo_id,)
            ).fetchone()
            if row:
                con.execute(
                    """UPDATE events SET title=?, date=?, time='', kind='todo',
                                        importance='normal', notes=? WHERE id=?""",
                    (title, due_date, notes.strip(), row["id"]),
                )
            else:
                con.execute(
                    """INSERT INTO events
                       (id,title,date,time,kind,importance,notes,uid,source,created_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (str(uuid.uuid4()), title, due_date, "", "todo", "normal",
                     notes.strip(), todo_id, "todo", now()),
                )

    def delete_todo_event(self, todo_id: str) -> None:
        """Remove the calendar entry linked to a to-do, if it exists."""
        with self.session() as con:
            con.execute("DELETE FROM events WHERE uid=? AND source='todo'", (todo_id,))

    def upcoming(self, limit: int = 8, start: str | None = None) -> list[dict]:
        start = start or date.today().isoformat()
        with self.session() as con:
            return self._rows(con.execute(
                """SELECT * FROM events WHERE date>=?
                   ORDER BY date, CASE WHEN time='' THEN '00:00' ELSE time END, title
                   LIMIT ?""",
                (start, int(limit)),
            ))

    def import_ics(self, text: str, source: str = "ics") -> tuple[int, int]:
        """Upsert parsed events by UID. Returns ``(added, updated)``."""
        events = parse_ics(text)
        added = updated = 0
        for event in events:
            with self.session() as con:
                row = con.execute(
                    "SELECT id FROM events WHERE uid=? AND source=?",
                    (event["uid"], source),
                ).fetchone()
                if row:
                    con.execute(
                        """UPDATE events SET title=?, date=?, time=?, notes=?,
                                            importance=? WHERE id=?""",
                        (event["title"], event["date"], event["time"],
                         event["notes"], event.get("importance", "normal"), row["id"]),
                    )
                    updated += 1
                else:
                    con.execute(
                        """INSERT INTO events
                           (id,title,date,time,kind,importance,notes,uid,source,created_at)
                           VALUES (?,?,?,?,?,?,?,?,?,?)""",
                        (str(uuid.uuid4()), event["title"], event["date"],
                         event["time"], "other", event.get("importance", "normal"),
                         event["notes"], event["uid"], source, now()),
                    )
                    added += 1
        return added, updated

    def export_ics(self) -> str:
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Lab Assistant//Lab Calendar//DE",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
        ]
        for event in self.list_events():
            stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
            uid = event["uid"] or f"{event['id']}@lab-assistant.local"
            lines.extend([
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{stamp}",
            ])
            if event["time"]:
                lines.append("DTSTART:" + event["date"].replace("-", "") + "T"
                             + event["time"].replace(":", "") + "00")
            else:
                lines.append("DTSTART;VALUE=DATE:" + event["date"].replace("-", ""))
            lines.append("SUMMARY:" + _escape(event["title"]))
            priority = {"high": "1", "normal": "5", "low": "9"}.get(
                event.get("importance", "normal"), "5"
            )
            lines.append(f"PRIORITY:{priority}")
            if event["notes"]:
                lines.append("DESCRIPTION:" + _escape(event["notes"]))
            lines.extend(["END:VEVENT"])
        lines.append("END:VCALENDAR")
        return "\r\n".join(lines) + "\r\n"

    # ----------------------------------------------------------------- accounts
    def list_accounts(self) -> list[dict]:
        with self.session() as con:
            return self._rows(con.execute(
                "SELECT * FROM accounts ORDER BY created_at, label"
            ))

    def add_account(self, provider: str, label: str, url: str) -> str:
        provider = provider.strip().lower()
        if provider not in ACCOUNT_PROVIDERS:
            raise ValueError("Unsupported calendar provider")
        label = label.strip()
        url = url.strip()
        if not label or not url:
            raise ValueError("Label and calendar URL are required")
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Calendar URL must be an http(s) address")
        identifier = str(uuid.uuid4())
        with self.session() as con:
            con.execute(
                "INSERT INTO accounts VALUES (?,?,?,?,?,?,?)",
                (identifier, provider, label, url, "", "", now()),
            )
        return identifier

    def delete_account(self, account_id: str) -> None:
        with self.session() as con:
            con.execute("DELETE FROM accounts WHERE id=?", (account_id,))

    def sync_account(self, account_id: str) -> tuple[int, int]:
        with self.session() as con:
            row = con.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()
        if not row:
            raise KeyError(account_id)
        account = dict(row)
        try:
            text = fetch_ics(account["url"])
            added, updated = self.import_ics(text, source="account:" + account_id)
        except ValueError as error:
            self._mark_account(account_id, "error", str(error))
            raise
        self._mark_account(account_id, "ok", f"{added} + / {updated} ~")
        return added, updated

    def _mark_account(self, account_id: str, status: str, detail: str) -> None:
        with self.session() as con:
            con.execute(
                "UPDATE accounts SET last_sync=?, status=? WHERE id=?",
                (now(), f"{status}: {detail}", account_id),
            )

    # ------------------------------------------------------------------ summary
    def week_range(self, day: date | None = None) -> tuple[str, str]:
        anchor = day or date.today()
        start = anchor - timedelta(days=anchor.weekday())
        return start.isoformat(), (start + timedelta(days=6)).isoformat()
