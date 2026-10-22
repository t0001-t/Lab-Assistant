import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lab_calculators import dilution, mastermix, molarity, neubauer
from lab_eln import ELNStore
from lab_exports import docx_bytes, pdf_bytes
from lab_synthesis import coverage_gaps, fallback_protocol, synthesize


class CalculatorTests(unittest.TestCase):
    def test_neubauer_live_dead_and_seeding(self):
        result = neubauer([100, 120, 80, 100], [10, 10, 10, 10], 2, 3,
                          target_cells=200_000, target_concentration_per_ml=500_000)
        self.assertEqual(result.live_per_ml, 2_000_000)
        self.assertEqual(result.total_live_cells, 6_000_000)
        self.assertAlmostEqual(result.viability_percent, 1000 / 11)
        self.assertAlmostEqual(result.stock_volume_ml, 0.1)
        self.assertAlmostEqual(result.medium_volume_ml, 0.3)

    def test_unknown_viability_and_invalid_dilution(self):
        self.assertIsNone(neubauer([20], None, 1, 1).viability_percent)
        with self.assertRaises(ValueError):
            dilution(solve="v1", c1=1, c2=2, v2=1)

    def test_molarity_all_unknowns(self):
        self.assertAlmostEqual(molarity(solve="m", concentration_mol_l=.1,
                                        volume_l=.01, molar_mass_g_mol=100), .1)
        self.assertAlmostEqual(molarity(solve="c", mass_g=.1,
                                        volume_l=.01, molar_mass_g_mol=100), .1)
        self.assertAlmostEqual(molarity(solve="V", mass_g=.1,
                                        concentration_mol_l=.1, molar_mass_g_mol=100), .01)
        self.assertAlmostEqual(molarity(solve="M", mass_g=.1,
                                        concentration_mol_l=.1, volume_l=.01), 100)

    def test_mastermix_scaling(self):
        rows = mastermix([("Buffer", 2), ("Enzyme", .5)], 10, 10)
        self.assertAlmostEqual(rows[0]["total_ul"], 22)
        self.assertAlmostEqual(rows[1]["total_ul"], 5.5)


class NotebookTests(unittest.TestCase):
    def test_hierarchy_media_and_protocol_survive_reopen(self):
        with tempfile.TemporaryDirectory() as temp:
            store = ELNStore(Path(temp))
            practicum = store.add_practicum("Biochemie", "Protein")
            day = store.add_day(practicum, "2026-10-21", "SDS-PAGE", "Dr. A", "B")
            entry = store.add_entry(day, "Messreihe", "text", "Probe A: 42 µL; 37 °C")
            media = store.add_media(entry, "notiz.txt", b"Original scan")
            self.assertEqual(store.read_media(media)[1], b"Original scan")
            self.assertEqual(store.list_days(practicum)[0]["id"], day)
            self.assertEqual(ELNStore(Path(temp)).list_entries(day)[0]["content"],
                             "Probe A: 42 µL; 37 °C")
            text, gaps = synthesize(store.get_day(day), store.list_entries(day), "hybrid", "de")
            self.assertEqual(gaps, [])
            self.assertIn("42 µL", text)
            self.assertIn(f"[source:{entry}]", text)
            store.save_protocol(day, "hybrid", "source", text, [entry])
            self.assertEqual(len(ELNStore(Path(temp)).list_protocols(day)), 1)

    def test_attachment_limits(self):
        with tempfile.TemporaryDirectory() as temp:
            store = ELNStore(Path(temp))
            practicum = store.add_practicum("P")
            day = store.add_day(practicum, "2026-10-21", "Tag")
            entry = store.add_entry(day, "N", "text", "Text")
            with self.assertRaises(ValueError):
                store.add_media(entry, "program.exe", b"x")

    def test_draft_is_autosaved_and_recovered(self):
        with tempfile.TemporaryDirectory() as temp:
            store = ELNStore(Path(temp))
            practicum = store.add_practicum("P")
            day = store.add_day(practicum, "2026-10-21", "Tag")
            store.save_draft(day, "Skizze", "Messwert 17")
            self.assertEqual(ELNStore(Path(temp)).get_draft(day)["content"], "Messwert 17")
            store.clear_draft(day)
            self.assertEqual(store.get_draft(day)["content"], "")


class SynthesisTests(unittest.TestCase):
    def setUp(self):
        self.day = {"title": "Zellkultur", "date": "2026-10-21", "supervisor": "A", "author": "B"}
        self.entries = [{"id": "source-1", "title": "Zählung", "kind": "text",
                         "content": "42 Zellen, 1,5 mL und 37 °C"}]

    def test_all_styles_keep_six_sections_and_exact_source(self):
        for style in ("bullet", "prose", "hybrid"):
            text, gaps = synthesize(self.day, self.entries, style, "de")
            self.assertEqual(gaps, [])
            self.assertEqual(len(re.findall(r"^## ", text, re.MULTILINE)), 7)
            self.assertIn("42 Zellen, 1,5 mL und 37 °C", text)

    def test_ai_omission_is_detected(self):
        gaps = coverage_gaps("## Titel, Datum und Personen\n42", self.entries, "de")
        self.assertIn("1,5", gaps)
        self.assertIn("source:source-1", gaps)

    def test_incomplete_ai_draft_falls_back_without_losing_sources(self):
        with patch("lab_synthesis._draft_ai", return_value="## Titel, Datum und Personen\n42"):
            text, gaps = synthesize(self.day, self.entries, "hybrid", "de", "ollama", model="test")
        self.assertTrue(gaps)
        self.assertIn("## Material und Methoden", text)
        self.assertIn("42 Zellen, 1,5 mL und 37 °C", text)

    def test_exports_open(self):
        text = fallback_protocol(self.day, self.entries, "hybrid", "de")
        self.assertTrue(pdf_bytes(text).startswith(b"%PDF"))
        self.assertTrue(docx_bytes(text).startswith(b"PK"))


if __name__ == "__main__":
    unittest.main()
