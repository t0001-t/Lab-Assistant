"""Plattformgerechte Datenverzeichnisse für die Desktop-App."""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "Lab Assistant"


def _app_data_dir() -> Path:
    """
    Gibt das plattformspezifische Anwendungsdatenverzeichnis zurück.
    - macOS: ~/Library/Application Support/Lab Assistant
    - Windows: %APPDATA%\\Lab Assistant
    - Linux: ~/.local/share/Lab Assistant (oder $XDG_DATA_HOME)
    """
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / APP_NAME


def get_data_dir() -> Path:
    """
    Liefert das finale Datenverzeichnis.
    Priorität:
    1. Umgebungsvariable LAB_ASSISTANT_DATA_DIR (für Tests/Entwicklung)
    2. Plattformspezifisches Verzeichnis
    """
    env = os.environ.get("LAB_ASSISTANT_DATA_DIR")
    if env:
        return Path(env).expanduser().resolve()

    data_dir = _app_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def ensure_data_dir() -> Path:
    """Erstellt das Datenverzeichnis falls nicht vorhanden und gibt es zurück."""
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


# Für Abwärtskompatibilität und Tests
def get_legacy_data_dir() -> Path:
    """Altes Standard-Verzeichnis (Projekt-Root / lab_data)."""
    return Path(__file__).parent / "lab_data"