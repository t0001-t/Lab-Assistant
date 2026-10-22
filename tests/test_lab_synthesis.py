"""Zero-loss and audit tests for the synthesis engine."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from lab_synthesis import (
    SECTIONS,
    SECTIONS_DE,
    build_prompt,
    coverage_gaps,
    coverage_report,
    fallback_protocol,
    protocol_stats,
    source_appendix,
    synthesize,
)

DAY = {
    "id": "day-1",
    "title": "Zellkultur",
    "date": "2026-10-21",
    "supervisor": "Dr. A",
    "author": "B",
}
ENTRIES = [
    {
        "id": "source-1",
        "title": "Zählung",
        "kind": "text",
        "content": "42 Zellen, 1,5 mL und 37 °C",
        "created_at": "2026-10-21T10:00:00+00:00",
        "attachments": [{"filename": "scan.png", "sha256": "abc123", "bytes": 128}],
    },
    {
        "id": "source-2",
        "title": "Diktat",
        "kind": "transcript",
        "content": "Abweichung: Inkubation 12 min statt 10 min.",
        "created_at": "2026-10-21T10:05:00+00:00",
        "attachments": [],
    },
]


class SourceAppendixTests(unittest.TestCase):
    def test_every_source_and_checksum_is_preserved(self) -> None:
        appendix = source_appendix(ENTRIES, "de")
        self.assertIn("Unveränderte Quellen", appendix)
        self.assertIn("42 Zellen, 1,5 mL und 37 °C", appendix)
        self.assertIn("Abweichung: Inkubation 12 min statt 10 min.", appendix)
        self.assertIn("[source:source-1]", appendix)
        self.assertIn("scan.png", appendix)
        self.assertIn("SHA-256: abc123", appendix)


class FallbackTests(unittest.TestCase):
    def test_all_styles_keep_six_sections_and_appendix(self) -> None:
        for style in ("bullet", "prose", "hybrid"):
            text = fallback_protocol(DAY, ENTRIES, style, "de")
            for title in SECTIONS_DE:
                self.assertIn(f"## {title}", text)
            self.assertIn("42 Zellen, 1,5 mL und 37 °C", text)
            self.assertIn("[source:source-1]", text)

    def test_english_sections(self) -> None:
        text = fallback_protocol(DAY, ENTRIES, "hybrid", "en")
        for title in SECTIONS:
            self.assertIn(f"## {title}", text)

    def test_unknown_style_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            fallback_protocol(DAY, ENTRIES, "unknown", "de")


class PromptTests(unittest.TestCase):
    def test_prompt_contains_zero_loss_rule_and_sources(self) -> None:
        prompt = build_prompt(DAY, ENTRIES, "hybrid", "de")
        self.assertIn("ZERO-LOSS RULE", prompt)
        self.assertIn("Titel, Datum und Personen", prompt)
        self.assertIn("42 Zellen, 1,5 mL und 37 °C", prompt)
        self.assertIn("[source:source-1]", prompt)
        self.assertIn("German", prompt)


class AuditTests(unittest.TestCase):
    def test_missing_sections_sources_and_numbers(self) -> None:
        report = coverage_report("## Titel, Datum und Personen\n42", ENTRIES, "de")
        self.assertIn("Material und Methoden", report["sections"])
        self.assertIn("source:source-1", report["sources"])
        self.assertIn("1,5", report["numbers"])
        self.assertIn("37", report["numbers"])

    def test_number_normalisation(self) -> None:
        draft = "\n".join(
            f"## {title}" for title in SECTIONS_DE
        ) + "\n[source:source-1] [source:source-2] 42 1.50 37 12 10"
        self.assertEqual(coverage_gaps(draft, ENTRIES, "de"), [])

    def test_gaps_are_sorted_and_unique(self) -> None:
        gaps = coverage_gaps("", ENTRIES, "de")
        self.assertEqual(gaps, sorted(set(gaps)))


class SynthesisTests(unittest.TestCase):
    def test_source_provider_appends_appendix(self) -> None:
        text, gaps = synthesize(DAY, ENTRIES, "hybrid", "de")
        self.assertEqual(gaps, [])
        self.assertIn("## Unveränderte Quellen", text)
        self.assertIn("42 Zellen, 1,5 mL und 37 °C", text)

    def test_complete_ai_draft_is_kept_and_sources_are_appended(self) -> None:
        draft = "\n".join(f"## {title}" for title in SECTIONS_DE)
        draft += ("\n[source:source-1] [source:source-2] 42 Zellen, 1,5 mL und 37 °C; "
                  "12 min statt 10 min; AI-ENTWURF")
        with patch("lab_synthesis._draft_ai", return_value=draft):
            text, gaps = synthesize(DAY, ENTRIES, "prose", "de", "ollama", model="test")
        self.assertEqual(gaps, [])
        self.assertIn("AI-ENTWURF", text)
        self.assertIn("## Unveränderte Quellen", text)
        self.assertIn("Abweichung: Inkubation 12 min statt 10 min.", text)

    def test_incomplete_ai_draft_falls_back_without_losing_sources(self) -> None:
        with patch("lab_synthesis._draft_ai", return_value="## Titel, Datum und Personen\n42"):
            text, gaps = synthesize(DAY, ENTRIES, "hybrid", "de", "ollama", model="test")
        self.assertTrue(gaps)
        self.assertIn("## Material und Methoden", text)
        self.assertIn("42 Zellen, 1,5 mL und 37 °C", text)
        self.assertIn("## Unveränderte Quellen", text)

    def test_stats(self) -> None:
        text, _ = synthesize(DAY, ENTRIES, "hybrid", "de")
        stats = protocol_stats(text, ENTRIES)
        self.assertEqual(stats["sections"], 6)
        self.assertEqual(stats["sources"], 2)
        self.assertGreater(stats["numbers"], 2)


if __name__ == "__main__":
    unittest.main()
