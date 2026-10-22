"""Tests for the local calendar store and iCalendar handling."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from lab_calendar import (
    CalendarStore,
    fetch_ics,
    month_matrix,
    parse_ics,
    shift_month,
)

SAMPLE = (
    "BEGIN:VCALENDAR\r\n"
    "VERSION:2.0\r\n"
    "PRODID:-//Test//DE\r\n"
    "BEGIN:VEVENT\r\n"
    "UID:event-1@example.org\r\n"
    "DTSTART:20261021T093000\r\n"
    "SUMMARY:Zellpassage; Probe A\r\n"
    "DESCRIPTION:Trypanblau\\nViabilität prüfen\r\n"
    "END:VEVENT\r\n"
    "BEGIN:VEVENT\r\n"
    "UID:event-2@example.org\r\n"
    "DTSTART;VALUE=DATE:20261022\r\n"
    "SUMMARY:Abgabe Protokoll\r\n"
    "END:VEVENT\r\n"
    "END:VCALENDAR"
)


class ICSReaderTests(unittest.TestCase):
    def test_parse_events_and_escapes(self) -> None:
        events = parse_ics(SAMPLE)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["date"], "2026-10-21")
        self.assertEqual(events[0]["time"], "09:30")
        self.assertEqual(events[0]["title"], "Zellpassage; Probe A")
        self.assertIn("Viabilität", events[0]["notes"])
        self.assertEqual(events[1]["time"], "")

    def test_rejects_non_calendar_text(self) -> None:
        with self.assertRaises(ValueError):
            parse_ics("just a note")

    def test_folded_lines_are_joined(self) -> None:
        text = SAMPLE.replace("SUMMARY:Abgabe Protokoll", "SUMMARY:Abgabe\r\n  Protokoll")
        events = parse_ics(text)
        self.assertEqual(events[1]["title"], "Abgabe Protokoll")

    def test_fetch_requires_http(self) -> None:
        with self.assertRaises(ValueError):
            fetch_ics("file:///etc/passwd")
        with self.assertRaises(ValueError):
            fetch_ics("ftp://example.org/calendar.ics")

    def test_month_matrix_attaches_events(self) -> None:
        events = [{"date": "2026-10-21", "time": "09:30", "title": "A", "kind": "other"},
                  {"date": "2026-10-21", "time": "08:00", "title": "B", "kind": "other"}]
        weeks = month_matrix(2026, 10, events)
        cells = [cell for week in weeks for cell in week if cell["date"] == date(2026, 10, 21)]
        self.assertEqual([event["title"] for event in cells[0]["events"]], ["B", "A"])
        self.assertEqual(weeks[0][0]["date"].weekday(), 0)

    def test_shift_month_wraps_year(self) -> None:
        self.assertEqual(shift_month(2026, 1, -1), (2025, 12))
        self.assertEqual(shift_month(2026, 12, 1), (2027, 1))
        self.assertEqual(shift_month(2026, 10, 0), (2026, 10))


class CalendarStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.store = CalendarStore(Path(self.temp.name))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_crud_and_ordering(self) -> None:
        first = self.store.add_event("Spät", "2026-10-21", "15:00", "practicum", "Notiz")
        self.store.add_event("Früh", "2026-10-21", "08:00", "deadline")
        events = self.store.list_events("2026-10-21", "2026-10-21")
        self.assertEqual([event["title"] for event in events], ["Früh", "Spät"])
        self.store.update_event(first, title="Verschoben", date="2026-10-22",
                                time="10:00", kind="submission", notes="")
        changed = self.store.get_event(first)
        self.assertEqual(changed["title"], "Verschoben")
        self.assertEqual(changed["kind"], "submission")
        self.store.delete_event(first)
        self.assertIsNone(self.store.get_event(first))

    def test_validation(self) -> None:
        with self.assertRaises(ValueError):
            self.store.add_event("", "2026-10-21")
        with self.assertRaises(ValueError):
            self.store.add_event("Titel", "21.10.2026")
        with self.assertRaises(ValueError):
            self.store.add_event("Titel", "2026-10-21", "9:30")
        with self.assertRaises(ValueError):
            self.store.add_event("Titel", "2026-10-21", "", "unknown")
        with self.assertRaises(ValueError):
            self.store.add_event("Titel", "2026-10-21", "", "other", importance="urgent")

    def test_importance_round_trip(self) -> None:
        event_id = self.store.add_event(
            "Wichtig", "2026-10-21", "09:30", "deadline", importance="high"
        )
        self.assertEqual(self.store.get_event(event_id)["importance"], "high")
        self.store.update_event(
            event_id, title="Wichtig", date="2026-10-21", time="09:30",
            kind="deadline", importance="low",
        )
        self.assertEqual(self.store.get_event(event_id)["importance"], "low")

    def test_todo_event_is_linked_and_removed(self) -> None:
        self.store.upsert_todo_event("todo-1", "Abgabe prüfen", "2026-10-24")
        events = self.store.list_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["kind"], "todo")
        self.assertEqual(events[0]["title"], "Abgabe prüfen")
        self.assertEqual(events[0]["date"], "2026-10-24")
        self.store.upsert_todo_event("todo-1", "Abgabe prüfen", "2026-10-25")
        moved = self.store.list_events()
        self.assertEqual(len(moved), 1)
        self.assertEqual(moved[0]["date"], "2026-10-25")
        self.store.delete_todo_event("todo-1")
        self.assertEqual(self.store.list_events(), [])

    def test_existing_calendar_gets_importance_column(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            database = Path(temp) / "lab_calendar.sqlite3"
            con = sqlite3.connect(database)
            con.executescript(
                """
                CREATE TABLE events (
                  id TEXT PRIMARY KEY, title TEXT NOT NULL, date TEXT NOT NULL,
                  time TEXT NOT NULL DEFAULT '', kind TEXT NOT NULL DEFAULT 'other',
                  notes TEXT NOT NULL DEFAULT '', uid TEXT NOT NULL DEFAULT '',
                  source TEXT NOT NULL DEFAULT 'manual', created_at TEXT NOT NULL
                );
                INSERT INTO events VALUES
                  ('old', 'Alt', '2026-10-21', '', 'other', '', '', 'manual', '2026-01-01');
                """
            )
            con.commit()
            con.close()
            migrated = CalendarStore(Path(temp))
            event = migrated.list_events()[0]
            self.assertEqual(event["importance"], "normal")

    def test_ics_priority_maps_to_importance(self) -> None:
        text = SAMPLE.replace(
            "UID:event-1@example.org\r\n",
            "UID:event-1@example.org\r\nPRIORITY:1\r\n",
        )
        events = parse_ics(text)
        self.assertEqual(events[0]["importance"], "high")
        self.store.add_event("Wichtig", "2026-10-21", "09:30", "deadline",
                             importance="high")
        self.assertIn("PRIORITY:1", self.store.export_ics())

    def test_import_upserts_by_uid(self) -> None:
        added, updated = self.store.import_ics(SAMPLE)
        self.assertEqual((added, updated), (2, 0))
        added_again, updated_again = self.store.import_ics(SAMPLE)
        self.assertEqual((added_again, updated_again), (0, 2))
        self.assertEqual(len(self.store.list_events()), 2)

    def test_export_round_trip(self) -> None:
        self.store.add_event("Zellpassage", "2026-10-21", "09:30", "incubation",
                             "Probe A, 37 °C")
        exported = self.store.export_ics()
        self.assertIn("BEGIN:VCALENDAR", exported)
        self.assertIn("SUMMARY:Zellpassage", exported)
        self.assertIn("Probe A\\, 37 °C", exported)
        parsed = parse_ics(exported)
        self.assertEqual(parsed[0]["date"], "2026-10-21")
        self.assertEqual(parsed[0]["time"], "09:30")
        self.assertEqual(parsed[0]["notes"], "Probe A, 37 °C")

    def test_upcoming_filters_past(self) -> None:
        self.store.add_event("Vergangen", "2020-01-01")
        self.store.add_event("Künftig", "2099-01-01")
        titles = [event["title"] for event in self.store.upcoming()]
        self.assertEqual(titles, ["Künftig"])

    def test_accounts_validate_and_sync(self) -> None:
        with self.assertRaises(ValueError):
            self.store.add_account("unknown", "Test", "https://example.org/a.ics")
        with self.assertRaises(ValueError):
            self.store.add_account("ical", "Test", "not-a-url")
        identifier = self.store.add_account("google", "Uni", "https://example.org/a.ics")
        self.assertEqual(self.store.list_accounts()[0]["label"], "Uni")
        with patch("lab_calendar.fetch_ics", return_value=SAMPLE):
            added, updated = self.store.sync_account(identifier)
        self.assertEqual((added, updated), (2, 0))
        account = self.store.list_accounts()[0]
        self.assertTrue(account["last_sync"])
        self.assertTrue(account["status"].startswith("ok"))
        with patch("lab_calendar.fetch_ics", side_effect=ValueError("down")), self.assertRaises(ValueError):
            self.store.sync_account(identifier)
        self.assertTrue(self.store.list_accounts()[0]["status"].startswith("error"))
        self.store.delete_account(identifier)
        self.assertEqual(self.store.list_accounts(), [])


if __name__ == "__main__":
    unittest.main()
