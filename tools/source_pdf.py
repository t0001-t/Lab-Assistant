"""Quellcode als sauber gesetztes PDF ausgeben.

Aufruf:
    .venv/bin/python tools/source_pdf.py app.py exports/app_py.pdf

Erzeugt ein A4-PDF mit Syntaxhervorhebung, Zeilennummern und Seitenzahlen.
Benötigt reportlab (nur für dieses Werkzeug, nicht für die App):

    .venv/bin/python -m pip install reportlab
"""

from __future__ import annotations

import builtins
import io
import keyword
import sys
import tokenize
from datetime import datetime
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

MM = 72 / 25.4
PAGE_W, PAGE_H = A4
MARGIN_X = 13 * MM
MARGIN_TOP = 14 * MM
MARGIN_BOTTOM = 13 * MM
GUTTER = 16.0
FONT_SIZE = 7.2
LEADING = 9.4

INK = HexColor("#1f2328")
MUTED = HexColor("#8b949e")
RULE = HexColor("#d8dee9")
ACCENT = HexColor("#0b4f8a")

COLORS = {
    "code": HexColor("#1f2328"),
    "comment": HexColor("#6e7781"),
    "string": HexColor("#0a7d33"),
    "keyword": HexColor("#a626a4"),
    "number": HexColor("#b35900"),
    "builtin": HexColor("#0550ae"),
    "defname": HexColor("#0550ae"),
    "decorator": HexColor("#8250df"),
}

BOLD_KINDS = {"keyword", "defname"}

FONT_FILES = {
    "Mono": ("/System/Library/Fonts/Supplemental/Courier New.ttf", "Courier"),
    "Mono-Bold": ("/System/Library/Fonts/Supplemental/Courier New Bold.ttf", "Courier-Bold"),
    "Mono-Italic": ("/System/Library/Fonts/Supplemental/Courier New Italic.ttf", "Courier-Oblique"),
}
FONT_NAMES: dict[str, str] = {}


def register_fonts() -> None:
    """Courier New aus macOS einbetten, sonst auf die PDF-Standardschrift zurückfallen."""
    for name, (path, fallback) in FONT_FILES.items():
        file = Path(path)
        registered = False
        if file.exists():
            try:
                pdfmetrics.registerFont(TTFont(name, str(file)))
                registered = True
            except Exception:  # noqa: BLE001 - defekte Systemdatei nicht fatal
                registered = False
        FONT_NAMES[name] = name if registered else fallback


def font(kind: str) -> str:
    if kind == "comment":
        return FONT_NAMES["Mono-Italic"]
    return FONT_NAMES["Mono-Bold"] if kind in BOLD_KINDS else FONT_NAMES["Mono"]


def span_kinds(source: str) -> list[list[str]]:
    """Pro Zeichen eine Kategorie bestimmen (Tokenizing über das stdlib-Modul)."""
    lines = source.splitlines()
    kinds: list[list[str]] = [["code"] * len(line) for line in lines]

    def paint(row: int, start: int, end: int, kind: str) -> None:
        if not 0 <= row < len(kinds):
            return
        line = kinds[row]
        for index in range(max(0, start), min(end, len(line))):
            line[index] = kind

    fstring_types = {
        getattr(tokenize, "FSTRING_START", -1),
        getattr(tokenize, "FSTRING_MIDDLE", -1),
        getattr(tokenize, "FSTRING_END", -1),
    }
    builtin_names = {name for name in dir(builtins) if not name.startswith("_")}
    previous: str | None = None

    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for token in tokens:
            ttype, text, start, end, _ = token
            row, col = start

            if ttype == tokenize.COMMENT:
                kind = "comment"
            elif ttype == tokenize.STRING or ttype in fstring_types:
                kind = "string"
            elif ttype == tokenize.NUMBER:
                kind = "number"
            elif ttype == tokenize.NAME and text in keyword.kwlist:
                kind = "keyword"
            elif ttype == tokenize.NAME and previous == "def_or_class":
                kind = "defname"
            elif ttype == tokenize.NAME and previous == "at":
                kind = "decorator"
            elif ttype == tokenize.NAME and text in builtin_names:
                kind = "builtin"
            else:
                kind = "code"

            if ttype in {tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENCODING}:
                continue

            if start[0] == end[0]:
                paint(row, col, end[1], kind)
            else:
                paint(row, col, len(lines[row]) if row < len(lines) else 0, kind)
                for middle in range(row + 1, end[0]):
                    paint(middle, 0, len(lines[middle]) if middle < len(lines) else 0, kind)
                paint(end[0], 0, end[1], kind)

            if ttype == tokenize.NAME and text in {"def", "class"}:
                previous = "def_or_class"
            elif ttype == tokenize.OP and text == "@":
                previous = "at"
            else:
                previous = None
    except (tokenize.TokenError, IndentationError):
        pass
    return kinds


def line_runs(line: str, kinds: list[str]) -> list[tuple[str, str]]:
    """Zusammenhängende Abschnitte gleicher Kategorie."""
    runs: list[tuple[str, str]] = []
    for char, kind in zip(line, kinds, strict=False):
        if runs and runs[-1][0] == kind:
            runs[-1] = (kind, runs[-1][1] + char)
        else:
            runs.append((kind, char))
    return runs


class Listing:
    """Rendert eine Quelldatei seitenweise als Code-Liste."""

    def __init__(self, source_path: Path, title: str) -> None:
        source = source_path.read_text(encoding="utf-8")
        if "\t" in source:
            source = source.expandtabs(4)
        self.name = source_path.name
        self.source = source
        self.lines = source.splitlines()
        self.kinds = span_kinds(source)
        self.title = title
        self.stamp = datetime.now().strftime("%d.%m.%Y")
        self.total_pages = 0

    @property
    def max_chars(self) -> int:
        char_w = pdfmetrics.stringWidth("M", font("code"), FONT_SIZE)
        return max(40, int((PAGE_W - 2 * MARGIN_X - GUTTER) / char_w))

    def frame(self, pdf: canvas.Canvas, page: int, first: bool) -> float:
        pdf.setFillColor(MUTED)
        pdf.setFont(font("code"), 7)
        pdf.drawString(MARGIN_X, PAGE_H - MARGIN_TOP + 7, f"GelDoc Studio  ·  {self.name}")
        pdf.drawRightString(PAGE_W - MARGIN_X, PAGE_H - MARGIN_TOP + 7, f"Seite {page} von {self.total_pages}")
        pdf.setStrokeColor(RULE)
        pdf.setLineWidth(0.6)
        pdf.line(MARGIN_X, PAGE_H - MARGIN_TOP + 2, PAGE_W - MARGIN_X, PAGE_H - MARGIN_TOP + 2)

        y = PAGE_H - MARGIN_TOP - 14
        if first:
            pdf.setFillColor(INK)
            pdf.setFont(font("keyword"), 17)
            pdf.drawString(MARGIN_X, y, "GelDoc Studio")
            y -= 14
            pdf.setFillColor(ACCENT)
            pdf.setFont(font("code"), 10)
            pdf.drawString(MARGIN_X, y, f"{self.name} – {self.title}" if self.title else self.name)
            y -= 11
            pdf.setFillColor(MUTED)
            pdf.setFont(font("code"), 7.5)
            pdf.drawString(
                MARGIN_X,
                y,
                f"{len(self.lines)} Zeilen · {len(self.source)} Zeichen · Stand {self.stamp}",
            )
            y -= 6
            pdf.setStrokeColor(RULE)
            pdf.line(MARGIN_X, y, PAGE_W - MARGIN_X, y)
            y -= 10
        pdf.setFillColor(INK)
        return y

    def render(self, pdf: canvas.Canvas, draw: bool) -> int:
        page = 1
        y = self.frame(pdf, page, True)
        char_w = pdfmetrics.stringWidth("M", font("code"), FONT_SIZE)
        width = self.max_chars

        for number, line in enumerate(self.lines, start=1):
            starts = range(0, len(line), width) if line else [0]
            for part_index, start in enumerate(starts):
                chunk = line[start : start + width]
                if y < MARGIN_BOTTOM + 8:
                    pdf.showPage()
                    page += 1
                    y = self.frame(pdf, page, False)
                if part_index == 0:
                    pdf.setFillColor(MUTED)
                    pdf.setFont(font("code"), FONT_SIZE)
                    pdf.drawRightString(MARGIN_X + GUTTER - 7, y, str(number))
                if draw:
                    x = MARGIN_X + GUTTER
                    for kind, text in line_runs(chunk, self.kinds[number - 1][start : start + len(chunk)]):
                        pdf.setFillColor(COLORS[kind])
                        pdf.setFont(font(kind), FONT_SIZE)
                        pdf.drawString(x, y, text)
                        x += char_w * len(text)
                y -= LEADING
        return page

    def write(self, target: Path) -> None:
        probe = canvas.Canvas(io.BytesIO(), pagesize=A4)
        self.total_pages = self.render(probe, False)

        target.parent.mkdir(parents=True, exist_ok=True)
        pdf = canvas.Canvas(str(target), pagesize=A4)
        pdf.setTitle(f"{self.name} – GelDoc Studio")
        pdf.setAuthor("GelDoc Studio")
        pdf.setSubject(f"Quellcode {self.name}")
        self.render(pdf, True)
        pdf.save()
        print(f"{target} · {self.total_pages} Seiten · {len(self.lines)} Zeilen")


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit("Aufruf: python tools/source_pdf.py <quelle.py> <ziel.pdf> [Titel]")
    register_fonts()
    listing = Listing(Path(sys.argv[1]), sys.argv[3] if len(sys.argv) > 3 else "")
    listing.write(Path(sys.argv[2]))


if __name__ == "__main__":
    main()
