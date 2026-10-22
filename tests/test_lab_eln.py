"""Pure-module tests for the local electronic lab notebook."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from lab_eln import ELNStore


class ELNHierarchyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = ELNStore(self.root)
        self.practicum = self.store.add_practicum("Biochemie", "Proteinanalytik")
        self.day = self.store.add_day(
            self.practicum, "2026-10-21", "SDS-PAGE", "Dr. A", "B"
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_hierarchy_search_and_summary(self) -> None:
        entry = self.store.add_entry(self.day, "Messreihe", "text",
                                     "Probe A: 42 µL; 37 °C")
        self.assertEqual(self.store.list_practica()[0]["name"], "Biochemie")
        self.assertEqual(self.store.list_days(self.practicum)[0]["id"], self.day)
        results = self.store.search_entries("42 µL")
        self.assertEqual(results[0]["id"], entry)
        self.assertEqual(results[0]["day_title"], "SDS-PAGE")
        self.assertEqual(self.store.day_summary(self.day),
                         {"entries": 1, "attachments": 0, "protocols": 0})

    def test_edit_practicum_and_day(self) -> None:
        self.store.update_practicum(self.practicum, "Molekularbiologie", "DNA")
        self.store.update_day(self.day, date="2026-10-22", title="PCR",
                              supervisor="Dr. B", author="C")
        self.assertEqual(self.store.get_practicum(self.practicum)["name"],
                         "Molekularbiologie")
        changed = self.store.get_day(self.day)
        self.assertEqual((changed["date"], changed["title"]), ("2026-10-22", "PCR"))

    def test_media_checksum_and_delete_entry_removes_file(self) -> None:
        entry = self.store.add_entry(self.day, "Scan", "text", "Original")
        media_id = self.store.add_media(entry, "scan.txt", b"original bytes")
        item, data = self.store.read_media(media_id)
        self.assertEqual(data, b"original bytes")
        self.assertEqual(item["filename"], "scan.txt")
        stored = self.root / "media" / item["stored_name"]
        self.assertTrue(stored.exists())
        self.assertEqual(self.store.verify_media(), [])
        self.store.delete_entry(entry)
        self.assertFalse(stored.exists())
        self.assertEqual(self.store.list_entries(self.day), [])

    def test_checksum_mismatch_is_detected(self) -> None:
        entry = self.store.add_entry(self.day, "Scan", "text", "Original")
        media_id = self.store.add_media(entry, "scan.txt", b"original bytes")
        item, _ = self.store.read_media(media_id)
        (self.root / "media" / item["stored_name"]).write_bytes(b"tampered")
        self.assertEqual(self.store.verify_media(), [item["stored_name"]])
        with self.assertRaises(ValueError):
            self.store.read_media(media_id)

    def test_delete_day_and_practicum_cascade(self) -> None:
        first = self.store.add_entry(self.day, "A", "text", "eins")
        first_media = self.store.add_media(first, "a.txt", b"a")
        second_day = self.store.add_day(self.practicum, "2026-10-23", "Zweiter Tag")
        second = self.store.add_entry(second_day, "B", "text", "zwei")
        second_media = self.store.add_media(second, "b.txt", b"b")
        paths = [
            self.root / "media" / self.store.read_media(media_id)[0]["stored_name"]
            for media_id in (first_media, second_media)
        ]
        self.store.delete_day(self.day)
        self.assertIsNone(self.store.get_day(self.day))
        self.assertFalse(paths[0].exists())
        self.assertTrue(paths[1].exists())
        self.store.delete_practicum(self.practicum)
        self.assertEqual(self.store.list_practica(), [])
        self.assertFalse(paths[1].exists())

    def test_draft_and_protocol_survive_reopen(self) -> None:
        self.store.save_draft(self.day, "Skizze", "Messwert 17")
        reopened = ELNStore(self.root)
        self.assertEqual(reopened.get_draft(self.day)["content"], "Messwert 17")
        entry = reopened.add_entry(self.day, "Quelle", "text", "42 Zellen")
        protocol = reopened.save_protocol(self.day, "hybrid", "source",
                                          "# Protokoll\n42 Zellen", [entry])
        self.assertEqual(reopened.get_protocol(protocol)["content"], "# Protokoll\n42 Zellen")
        self.assertEqual(len(reopened.list_protocols(self.day)), 1)
        reopened.delete_protocol(protocol)
        self.assertEqual(reopened.list_protocols(self.day), [])

    def test_unsupported_and_oversized_media_are_rejected(self) -> None:
        entry = self.store.add_entry(self.day, "N", "text", "Text")
        with self.assertRaises(ValueError):
            self.store.add_media(entry, "program.exe", b"x")
        with self.assertRaises(ValueError):
            self.store.add_media(entry, "empty.txt", b"")

    def test_universal_import_accepts_unknown_document_extension(self) -> None:
        entry = self.store.add_entry(self.day, "Anhang", "text", "Original")
        media_id = self.store.add_media(entry, "sequencing.ab1", b"trace")
        item, data = self.store.read_media(media_id)
        self.assertEqual(item["filename"], "sequencing.ab1")
        self.assertEqual(data, b"trace")

    def test_folder_colours_and_todos_persist(self) -> None:
        self.assertEqual(self.store.get_practicum(self.practicum)["color"], "#8fc7b2")
        self.store.set_practicum_color(self.practicum, "#9cb9e8")
        reopened = ELNStore(self.root)
        self.assertEqual(reopened.get_practicum(self.practicum)["color"], "#9cb9e8")
        todo = reopened.add_todo("Abgabe prüfen", "2026-10-24")
        reopened.add_todo("Inkubator leeren")
        self.assertEqual(len(reopened.list_todos()), 2)
        reopened.set_todo_done(todo, True)
        tasks = reopened.list_todos()
        self.assertEqual(tasks[0]["text"], "Inkubator leeren")
        self.assertEqual(tasks[1]["done"], 1)
        reopened.delete_todo(todo)
        self.assertEqual([task["text"] for task in reopened.list_todos()],
                         ["Inkubator leeren"])


if __name__ == "__main__":
    unittest.main()
