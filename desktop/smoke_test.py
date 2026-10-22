"""Prüft den gebündelten Server einschließlich Start, App-Shell und Beenden."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="lab-assistant-app-test-") as temporary:
        root = Path(temporary)
        ready = root / "ready.json"
        with (root / "server.log").open("w+") as logfile:
            process = subprocess.Popen([str(args.binary.resolve()), "--app-home", str(root / "home"),
                                        "--ready-file", str(ready)], stdout=logfile, stderr=logfile,
                                       env={"PATH": "/usr/bin:/bin", "HOME": os.environ["HOME"]})
            url = None
            try:
                deadline = time.monotonic() + 90
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        logfile.seek(0)
                        raise RuntimeError(logfile.read())
                    if ready.exists():
                        url = json.loads(ready.read_text())["url"]
                        break
                    time.sleep(0.2)
                if url is None:
                    raise RuntimeError("Server nicht rechtzeitig bereit")
                for path, content in [("/_stcore/health", b"ok"), ("/", b"/pwa-runtime.js"),
                                      ("/static/manifest.json", b"Lab Assistant"),
                                      ("/static/sw.js", b"CACHE_VERSION"),
                                      ("/static/assets/icon-192.png", b"PNG")]:
                    with urllib.request.urlopen(url + path, timeout=10) as response:
                        assert response.status == 200, path
                        assert content in response.read(), path
                assert (root / "home/runtime/pwa_entrypoint.py").is_file()
                assert (root / "home/data").is_dir()
                print("PASS: eigenständiger Server ohne Python im PATH; HTTP, PWA-Dateien und Datenordner bereit", flush=True)
            finally:
                process.terminate()
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            assert not ready.exists(), "Bereitschaftsdatei wurde nicht entfernt"
            if url:
                try:
                    urllib.request.urlopen(url + "/_stcore/health", timeout=2)
                except (OSError, urllib.error.URLError):
                    print("PASS: Server und Kindprozess nach Beenden nicht mehr erreichbar", flush=True)
                else:
                    raise RuntimeError("Server läuft nach Beenden weiter")


if __name__ == "__main__":
    main()
