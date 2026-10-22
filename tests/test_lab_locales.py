"""Localisation invariants for the new modules."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from lab_locales import TR, missing_keys, tr

ROOT = Path(__file__).resolve().parents[1]


class LocaleTests(unittest.TestCase):
    def test_every_key_has_two_non_empty_values(self) -> None:
        for key, values in TR.items():
            self.assertIsInstance(values, tuple, key)
            self.assertEqual(len(values), 2, key)
            self.assertTrue(values[0].strip(), key)
            self.assertTrue(values[1].strip(), key)

    def test_missing_keys_is_empty_for_both_languages(self) -> None:
        self.assertEqual(missing_keys("de"), [])
        self.assertEqual(missing_keys("en"), [])

    def test_tr_selects_language(self) -> None:
        self.assertEqual(tr("app", "de"), "Lab Assistant")
        self.assertEqual(tr("calculators", "de"), "Laborrechner")
        self.assertEqual(tr("calculators", "en"), "Lab calculators")

    def test_all_used_keys_exist(self) -> None:
        used: set[str] = set()
        for filename in ("lab_pages.py", "lab_assistant.py", "lab_dashboard.py"):
            source = (ROOT / filename).read_text(encoding="utf-8")
            used.update(re.findall(r'\bT\("([^"]+)"\)', source))
            used.update(re.findall(r'\btr\("([^"]+)"', source))
        self.assertTrue(used)
        self.assertEqual(sorted(used - set(TR)), [])


if __name__ == "__main__":
    unittest.main()
