"""Baut eine eigenständige Apple-Silicon-App und das auslieferbare ZIP."""
from __future__ import annotations

import argparse
import os
import plistlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def run(*command: str) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT.parent / "releases")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    staging = ROOT / "desktop/staged-application"
    staging.mkdir(exist_ok=True)
    for file in ROOT.glob("*.py"):
        if file.name not in {"build_app.py", "generate_icons.py"}:
            shutil.copy2(file, staging / file.name)
    for name in ("assets", "components", ".streamlit"):
        shutil.copytree(ROOT / name, staging / name, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
    os.environ.setdefault("PYINSTALLER_CONFIG_DIR", str(output / ".pyinstaller-cache"))
    run(sys.executable, "-m", "PyInstaller", "--noconfirm", "--distpath", str(output / "backend-build"),
        "--workpath", str(output / ".build"), str(ROOT / "desktop/backend.spec"))
    app = Path(tempfile.mkdtemp(prefix="lab-assistant-macos-")) / "Lab Assistant.app"
    contents = app / "Contents"
    (contents / "MacOS").mkdir(parents=True, exist_ok=True)
    (contents / "Resources").mkdir(exist_ok=True)
    shutil.copytree(output / "backend-build/LabAssistantServer", contents / "Resources/backend",
                    dirs_exist_ok=True, symlinks=True)
    sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
    run("xcrun", "swiftc", str(ROOT / "desktop/App.swift"), "-o", str(contents / "MacOS/LabAssistant"),
        "-sdk", sdk, "-target", "arm64-apple-macos14.0", "-module-cache-path", str(output / ".swift-cache"),
        "-framework", "Cocoa", "-framework", "WebKit")
    with Image.open(ROOT / "assets/icon.png") as icon:
        icon.save(contents / "Resources/AppIcon.icns")
    info = {"CFBundleName": "Lab Assistant", "CFBundleDisplayName": "Lab Assistant",
            "CFBundleIdentifier": "de.labassistant.pwa.desktop", "CFBundleExecutable": "LabAssistant",
            "CFBundlePackageType": "APPL", "CFBundleShortVersionString": "1.0.3", "CFBundleVersion": "4",
            "CFBundleIconFile": "AppIcon.icns", "LSMinimumSystemVersion": "14.0",
            "NSHighResolutionCapable": True, "NSPrincipalClass": "NSApplication",
            "NSAppTransportSecurity": {"NSAllowsLocalNetworking": True}}
    with (contents / "Info.plist").open("wb") as handle:
        plistlib.dump(info, handle)
    subprocess.run(["xattr", "-d", "com.apple.FinderInfo", str(app)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    run("codesign", "--force", "--deep", "--sign", "-", str(app))
    run("codesign", "--verify", "--deep", "--strict", str(app))
    archive = output / "Lab_Assistant_Mac_AppleSilicon_1.0.3.zip"
    run("ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", str(app), str(archive))
    print(archive)


if __name__ == "__main__":
    main()
