"""Vergleicht die unverändert übernommenen Codeblöcke mit der PWA-Vorlage."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    expected = json.loads((ROOT / "VORLAGEN_DATEIEN.json").read_text())
    mismatches = []
    for name, digest in expected.items():
        actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        print(f"{'IDENTISCH' if actual == digest else 'ABWEICHUNG'} {name}")
        if actual != digest:
            mismatches.append(name)
    if mismatches:
        raise SystemExit("Abweichungen: " + ", ".join(mismatches))


if __name__ == "__main__":
    main()
