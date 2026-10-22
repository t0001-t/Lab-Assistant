"""Traceable notebook synthesis and optional local/API transcription and drafting.

The module is deliberately independent of Streamlit so that the complete
protocol pipeline can be tested without a running UI. AI output is treated as
untrusted: every draft is checked for section/source/number coverage and the
unaltered source entries are always appended to the result.
"""

from __future__ import annotations

import io
import re
import tempfile
from pathlib import Path

SECTIONS = [
    "Title, date and personnel",
    "Aim and question",
    "Materials and methods",
    "Raw data and observations",
    "Results and analysis",
    "Discussion and deviations",
]
SECTIONS_DE = [
    "Titel, Datum und Personen",
    "Ziel und Fragestellung",
    "Material und Methoden",
    "Rohdaten und Beobachtungen",
    "Ergebnisse und Auswertung",
    "Diskussion und Abweichungen",
]
NUMBER_RE = re.compile(r"(?<![\w.])[+-]?(?:\d+(?:[.,]\d+)?|\.\d+)(?:[eE][+-]?\d+)?(?![\w.])")


def _normalise_number(token: str) -> str:
    """Comparison form for measurements: 1,50 and 1.5 are the same value."""
    value = token.replace(",", ".")
    try:
        number = float(value)
    except ValueError:
        return value
    if number == int(number):
        return str(int(number))
    return format(number, ".15g")


def _normalise_number_text(text: str) -> str:
    return NUMBER_RE.sub(lambda match: _normalise_number(match.group(0)), text)


def ocr_image(data: bytes, lang: str) -> str:
    """Extract text from a scan with local Tesseract."""
    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Install optional OCR requirements and the Tesseract system package") from exc
    image = Image.open(io.BytesIO(data))
    image.load()
    if image.width * image.height > 40_000_000:
        raise ValueError("Image too large for OCR")
    try:
        return pytesseract.image_to_string(
            image, lang="deu+eng" if lang == "de" else "eng"
        ).strip()
    except pytesseract.TesseractError as exc:
        raise RuntimeError("Tesseract or its language data are unavailable") from exc


def transcribe_audio(data: bytes, filename: str, backend: str, *,
                     api_key: str = "", model: str = "small") -> str:
    """Transcribe WAV/MP3/M4A locally with Whisper or through the OpenAI API."""
    suffix = Path(filename).suffix.lower()
    if suffix not in {".wav", ".mp3", ".m4a"}:
        raise ValueError("Unsupported audio format")
    if not data or len(data) > 25 * 1024 * 1024:
        raise ValueError("Audio must be between 1 byte and 25 MB")
    if backend == "local":
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError("Install optional faster-whisper requirements") from exc
        with tempfile.NamedTemporaryFile(suffix=suffix) as temp:
            temp.write(data)
            temp.flush()
            segments, _ = WhisperModel(
                model, device="auto", compute_type="int8"
            ).transcribe(temp.name)
            return " ".join(segment.text.strip() for segment in segments).strip()
    if backend == "openai":
        if not api_key:
            raise ValueError("An API key is required")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install optional OpenAI requirements") from exc
        payload = io.BytesIO(data)
        payload.name = Path(filename).name
        return OpenAI(api_key=api_key).audio.transcriptions.create(
            model="whisper-1", file=payload
        ).text.strip()
    raise ValueError("Unknown transcription backend")


def source_appendix(entries: list[dict], lang: str) -> str:
    """Render every source entry verbatim, including attachment checksums."""
    heading = "Unveränderte Quellen" if lang == "de" else "Unaltered source entries"
    chunks = [f"## {heading}"]
    for index, entry in enumerate(entries, 1):
        title = entry.get("title") or entry.get("kind") or "Note"
        kind = entry.get("kind", "text")
        created = entry.get("created_at", "")
        meta = f"Art: {kind}" if lang == "de" else f"Kind: {kind}"
        if created:
            meta += f" · {'erfasst' if lang == 'de' else 'recorded'}: {created}"
        attached = "\n".join(
            f"- {item['filename']} | SHA-256: {item['sha256']} | {item['bytes']} bytes"
            for item in entry.get("attachments", [])
        )
        body = entry.get("content", "")
        chunks.append(
            f"### {index}. {title} [source:{entry['id']}]\n\n"
            f"*{meta}*\n\n{body}" + (f"\n\n{attached}" if attached else "")
        )
    return "\n\n".join(chunks)


def _metadata_line(day: dict, style: str, lang: str) -> str:
    supervisor = day.get("supervisor") or ("Nicht angegeben" if lang == "de" else "Not stated")
    author = day.get("author") or ("Nicht angegeben" if lang == "de" else "Not stated")
    if style == "prose":
        if lang == "de":
            return (f"Der Versuch **{day.get('title', '')}** wurde am {day.get('date', '')} "
                    f"von {author} unter Betreuung von {supervisor} durchgeführt.")
        return (f"The experiment **{day.get('title', '')}** was performed on {day.get('date', '')} "
                f"by {author} under the supervision of {supervisor}.")
    labels = (
        ("Titel", "Datum", "Betreuer", "Bearbeiter")
        if lang == "de" else ("Title", "Date", "Supervisor", "Author")
    )
    values = (day.get("title", ""), day.get("date", ""), supervisor, author)
    return "\n".join(f"- **{label}:** {value}" for label, value in zip(labels, values))


def fallback_protocol(day: dict, entries: list[dict], style: str, lang: str) -> str:
    """Build a complete, source-faithful protocol without an AI provider."""
    if style not in {"bullet", "prose", "hybrid"}:
        raise ValueError("Unknown protocol style")
    titles = SECTIONS_DE if lang == "de" else SECTIONS
    unknown = "Nicht angegeben; bitte ergänzen." if lang == "de" else "Not stated; please complete."
    title = day.get("title", "")
    pieces = [f"# {title}", f"## {titles[0]}\n\n{_metadata_line(day, style, lang)}"]

    for section in (titles[1], titles[2]):
        pieces.append(f"## {section}\n\n{unknown}")

    raw: list[str] = []
    for index, entry in enumerate(entries, 1):
        label = f"{index}. {entry.get('title') or entry.get('kind')} [source:{entry['id']}]"
        content = entry.get("content", "")
        if style == "prose":
            raw.append(f"**{label}.** {content}")
        else:
            indented = content.replace("\n", "\n  ")
            raw.append(f"- **{label}**\n\n  {indented}")
    pieces.append(f"## {titles[3]}\n\n" + ("\n\n".join(raw) if raw else unknown))

    for section in (titles[4], titles[5]):
        pieces.append(f"## {section}\n\n{unknown}")
    return "\n\n".join(pieces)


def build_prompt(day: dict, entries: list[dict], style: str, lang: str) -> str:
    """Strict zero-loss prompt. The unaltered sources are appended separately."""
    titles = SECTIONS_DE if lang == "de" else SECTIONS
    raw = source_appendix(entries, lang)
    style_instruction = {
        "bullet": "Use detailed, hierarchically nested bullet points throughout.",
        "prose": ("Use coherent academic prose throughout. Use tables only where they make raw "
                  "measurements clearer."),
        "hybrid": ("Use prose for aim, methods and discussion; use hierarchical bullet points "
                   "or tables for pipetting schemes, measurement series and error analysis."),
    }[style]
    language = "German" if lang == "de" else "English"
    return (
        f"Write a scientific lab protocol in {language}.\n"
        "Use exactly these six H2 headings, in this order: " + "; ".join(titles) + ".\n"
        + style_instruction + "\n"
        "ZERO-LOSS RULE: Every number, unit, concentration, temperature, duration, reagent, "
        "sample identifier, observation, deviation, warning and marginal note from the sources "
        "must appear unchanged in the protocol. Do not summarise away details, do not round, "
        "do not silently correct suspicious values, and do not invent missing facts. If a "
        "section has no source information, write explicitly that it was not stated.\n"
        "Cite every source at least once with its [source:ID] marker. Do not add a source "
        "appendix; the application appends the unaltered sources automatically.\n"
        f"Day metadata: {day!r}\n\n{raw}"
    )


def _draft_ai(prompt: str, provider: str, *, model: str, api_key: str = "") -> str:
    if provider == "ollama":
        import json
        from urllib.request import Request, urlopen
        request = Request(
            "http://127.0.0.1:11434/api/generate",
            data=json.dumps({"model": model, "prompt": prompt, "stream": False}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=180) as response:
            return json.load(response)["response"]
    if provider == "openai":
        if not api_key:
            raise ValueError("An API key is required")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install optional OpenAI requirements") from exc
        response = OpenAI(api_key=api_key).responses.create(
            model=model, input=prompt, store=False
        )
        return response.output_text
    raise ValueError("Unknown synthesis provider")


def coverage_report(draft: str, entries: list[dict], lang: str) -> dict[str, list[str]]:
    """Audit an AI draft for missing sections, sources, numbers and attachments."""
    missing_sections = [
        title for title in (SECTIONS_DE if lang == "de" else SECTIONS)
        if f"## {title}" not in draft
    ]
    missing_sources = [
        f"source:{entry['id']}" for entry in entries
        if f"[source:{entry['id']}]" not in draft
    ]
    normalised_draft = _normalise_number_text(draft)
    missing_numbers: list[str] = []
    seen: set[str] = set()
    for entry in entries:
        for number in NUMBER_RE.findall(entry.get("content", "")):
            key = _normalise_number(number)
            if key not in seen and key not in normalised_draft:
                seen.add(key)
                missing_numbers.append(number)
    return {
        "sections": missing_sections,
        "sources": missing_sources,
        "numbers": missing_numbers,
    }


def coverage_gaps(draft: str, entries: list[dict], lang: str) -> list[str]:
    """Flatten the audit report into a stable, human-readable list."""
    report = coverage_report(draft, entries, lang)
    return sorted(set(
        report["sections"] + report["sources"] + report["numbers"]
    ))


def synthesize(day: dict, entries: list[dict], style: str, lang: str,
               provider: str = "source", *, model: str = "",
               api_key: str = "") -> tuple[str, list[str]]:
    """Create a protocol and always append the untouched source entries.

    If the AI draft fails the coverage audit, the complete source-based
    template is used instead. The returned gap list explains any fallback.
    """
    base = fallback_protocol(day, entries, style, lang)
    if provider == "source":
        draft, gaps = base, []
    else:
        draft = _draft_ai(
            build_prompt(day, entries, style, lang), provider, model=model, api_key=api_key
        ).strip()
        gaps = coverage_gaps(draft, entries, lang)
        if gaps:
            draft = base
    appendix = source_appendix(entries, lang)
    return draft + "\n\n---\n\n" + appendix + "\n", gaps


def protocol_stats(text: str, entries: list[dict]) -> dict[str, int]:
    """Small, transparent quality indicator for the review panel."""
    return {
        "sections": sum(f"## {title}" in text for title in SECTIONS + SECTIONS_DE),
        "sources": sum(f"[source:{entry['id']}]" in text for entry in entries),
        "numbers": len(NUMBER_RE.findall(text)),
    }
