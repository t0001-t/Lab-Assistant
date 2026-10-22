"""Markdown subset and export tests for protocols."""

from __future__ import annotations

import io
import unittest
import zipfile

from lab_exports import docx_bytes, parse_markdown, pdf_bytes

SAMPLE = """# Titel

Ein **fetter** Satz mit *kursiv* und `code` sowie [Link](https://example.org).

## Material und Methoden

- Puffer 10 µL
  - Unterpunkt
1. Erster Schritt
2. Zweiter Schritt

| Probe | Wert |
|---|---:|
| A | 1,5 |
| B | 42 |

> Hinweis

---
"""


class MarkdownParserTests(unittest.TestCase):
    def test_block_types(self) -> None:
        kinds = [block.kind for block in parse_markdown(SAMPLE)]
        self.assertIn("heading", kinds)
        self.assertIn("paragraph", kinds)
        self.assertIn("bullet", kinds)
        self.assertIn("numbered", kinds)
        self.assertIn("table", kinds)
        self.assertIn("quote", kinds)
        self.assertIn("rule", kinds)
        table = next(block for block in parse_markdown(SAMPLE) if block.kind == "table")
        self.assertEqual(table.rows[0], ("Probe", "Wert"))
        self.assertEqual(table.rows[2], ("B", "42"))

    def test_empty_markdown(self) -> None:
        self.assertEqual(parse_markdown(""), [])
        self.assertTrue(pdf_bytes("").startswith(b"%PDF"))


class ExportTests(unittest.TestCase):
    def test_pdf_and_docx_open(self) -> None:
        pdf = pdf_bytes(SAMPLE)
        docx = docx_bytes(SAMPLE)
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertTrue(docx.startswith(b"PK"))
        self.assertGreater(len(pdf), 1000)
        self.assertGreater(len(docx), 5000)

    def test_docx_contains_table_values(self) -> None:
        document = zipfile.ZipFile(io.BytesIO(docx_bytes(SAMPLE)))
        xml = document.read("word/document.xml").decode("utf-8")
        self.assertIn("Titel", xml)
        self.assertIn("Probe", xml)
        self.assertIn("1,5", xml)
        self.assertIn("42", xml)

    def test_protocol_export_with_unicode_and_long_text(self) -> None:
        text = "# Protokoll\n\n" + ("µL °C ≥ 10⁴ Zellen  \n" * 100)
        self.assertTrue(pdf_bytes(text).startswith(b"%PDF"))
        self.assertTrue(docx_bytes(text).startswith(b"PK"))


if __name__ == "__main__":
    unittest.main()
