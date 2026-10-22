#!/usr/bin/env python3
"""Build-Script für Windows (.exe) und macOS (.app/.dmg)."""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
BUILD = ROOT / "build"

def run(cmd: list[str], cwd: Path = ROOT) -> None:
    print(f">>> {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)

def clean():
    for p in (DIST, BUILD):
        if p.exists():
            shutil.rmtree(p)
    for spec in ROOT.glob("*.spec"):
        if spec.name != "lab_assistant.spec":
            spec.unlink()

def build_pyinstaller():
    run([sys.executable, "-m", "PyInstaller", "--clean", "lab_assistant.spec"])

def create_dmg():
    """macOS: .app → .dmg (nur auf macOS)."""
    if sys.platform != "darwin":
        return
    app = DIST / "Lab Assistant.app"
    dmg = DIST / "Lab_Assistant_1.0.0.dmg"
    if app.exists():
        run([
            "hdiutil", "create", "-volname", "Lab Assistant",
            "-srcfolder", str(app), "-ov", "-format", "UDZO",
            str(dmg)
        ])
        print(f"✅ DMG erstellt: {dmg}")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true", help="Vorher dist/build löschen")
    parser.add_argument("--dmg", action="store_true", help="macOS: .dmg erzeugen")
    args = parser.parse_args()

    if args.clean:
        clean()

    # PyInstaller baut automatisch für die aktuelle Plattform
    build_pyinstaller()

    if args.dmg and sys.platform == "darwin":
        create_dmg()

    print("\n✅ Fertig!")
    print(f"   Artefakte in: {DIST}")

if __name__ == "__main__":
    main()