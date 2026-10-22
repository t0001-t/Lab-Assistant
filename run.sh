#!/usr/bin/env bash
# Startet den Lab Assistant in einer lokalen Umgebung.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
./.venv/bin/python -m pip install --quiet --upgrade pip
./.venv/bin/python -m pip install --quiet -r requirements.txt

exec ./.venv/bin/python -m streamlit run lab_assistant.py "$@"
