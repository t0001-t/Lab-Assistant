# lab_assistant.spec
# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

ROOT = Path(__file__).parent

# ---------- 1. DATEN SAMMELN ----------
datas = [
    (str(ROOT / "components"), "components"),
    (str(ROOT / "assets"), "assets"),
    (str(ROOT / ".streamlit"), ".streamlit"),
    (str(ROOT / "locales.py"), "."),
    (str(ROOT / "models.py"), "."),
    (str(ROOT / "workflow.py"), "."),
    (str(ROOT / "canvas_renderer.py"), "."),
    (str(ROOT / "editor_component.py"), "."),
    (str(ROOT / "image_processing.py"), "."),
    (str(ROOT / "lab_assistant.py"), "."),
    (str(ROOT / "lab_dashboard.py"), "."),
    (str(ROOT / "lab_calendar.py"), "."),
    (str(ROOT / "lab_pages.py"), "."),
    (str(ROOT / "lab_eln.py"), "."),
    (str(ROOT / "lab_calculators.py"), "."),
    (str(ROOT / "lab_exports.py"), "."),
    (str(ROOT / "lab_gel_bridge.py"), "."),
    (str(ROOT / "lab_synthesis.py"), "."),
    (str(ROOT / "lab_theme.py"), "."),
    (str(ROOT / "lab_locales.py"), "."),
    (str(ROOT / "demo_project.py"), "."),
    (str(ROOT / "ruff.toml"), "."),
]

# ---------- 2. BINÄREN (falls OpenCV später doch gebraucht wird) ----------
binaries = []

# ---------- 3. HIDDEN IMPORTS ----------
hiddenimports = [
    "streamlit", "streamlit.runtime", "streamlit.elements",
    "streamlit.components.v1", "streamlit.web.bootstrap",
    "streamlit.web.server.routes",
    "pydantic", "pydantic.v1", "pydantic_core",
    "numpy", "pandas", "PIL", "PIL._imaging",
    "reportlab", "reportlab.pdfbase", "reportlab.pdfbase.ttfonts",
    "docx", "docx.oxml",
    "sqlite3", "csv", "json", "pathlib", "hashlib", "uuid",
    "datetime", "threading", "queue", "email.mime.multipart",
    "email.mime.text", "html", "urllib.parse", "base64", "io",
    "math", "statistics", "collections", "itertools", "functools",
    "dataclasses", "typing", "inspect", "textwrap", "re", "os", "sys",
    "subprocess", "tempfile", "shutil", "glob", "fnmatch", "time",
    "calendar", "decimal", "fractions", "numbers", "string",
    "unicodedata", "warnings", "contextlib", "abc", "enum",
    "operator", "copy", "pickle", "shelve", "marshal", "reprlib",
    "weakref", "types", "importlib", "importlib.metadata",
    "importlib.resources", "pkgutil", "modulefinder", "runpy",
    "zipfile", "tarfile", "gzip", "bz2", "lzma", "hmac", "secrets",
    "ssl", "socket", "select", "selectors", "asyncio",
    "concurrent.futures", "multiprocessing", "logging",
    "logging.handlers", "argparse", "getopt", "optparse", "cmd",
    "shlex", "configparser", "netrc", "plistlib", "tomllib",
    "xml.etree.ElementTree", "html.parser", "html.entities",
    "urllib.request", "urllib.response", "urllib.error",
    "http.client", "http.server", "email.message", "email.parser",
    "email.generator", "mimetypes", "binascii", "quopri", "uu",
    "colorsys", "zoneinfo", "stat", "filecmp", "linecache",
    "difflib", "stringprep", "readline", "rlcompleter",
]

# ---------- 4. EXCLUDES ----------
excludes = [
    "pytest", "unittest", "test", "tests", "ipython", "jupyter",
    "notebook", "jupyterlab", "matplotlib", "seaborn", "plotly",
    "bokeh", "scipy", "sklearn", "skimage", "torch", "tensorflow",
    "jax", "flax", "cv2", "PIL.ImageShow", "PIL.ImageQt",
    "tkinter", "tcl", "ttk", "setuptools", "pip", "wheel",
    "pkg_resources", "sphinx", "docutils", "jinja2", "markdown",
    "black", "ruff", "flake8", "mypy", "ipykernel", "ipywidgets",
]

# ---------- 5. ICON ----------
icon_path = "assets/icon.ico" if sys.platform == "win32" else "assets/icon.icns"

# ---------- 6. ANALYSIS ----------
a = Analysis(
    ["lab_assistant.py"],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# ---------- 7. PYZ ----------
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# ---------- 8. EXE / APP ----------
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Lab Assistant",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path if Path(icon_path).exists() else None,
)

# ---------- 9. MACOS APP BUNDLE ----------
if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="Lab Assistant.app",
        icon="assets/icon.icns" if Path("assets/icon.icns").exists() else None,
        bundle_identifier="com.labassistant.app",
        info_plist={
            "NSHighResolutionCapable": "True",
            "LSMinimumSystemVersion": "10.15",
            "CFBundleShortVersionString": "1.0.0",
            "CFBundleVersion": "1",
            "NSHumanReadableCopyright": "© 2026 Tabea Homann",
        },
    )