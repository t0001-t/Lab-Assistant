"""Erzeugt fontunabhängige SVG-Masken aus Streamlits mitgelieferten Symbolen."""
from __future__ import annotations

import json
import re
from pathlib import Path

import streamlit
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
font_path = next((Path(streamlit.__file__).parent / "static/static/media").glob("MaterialSymbols*.woff2"))
font = TTFont(font_path)
inverse = {name: chr(code) for code, name in font.getBestCmap().items() if code < 128}
ligatures = {}
for lookup in font["GSUB"].table.LookupList.Lookup:
    for subtable in lookup.SubTable:
        subtable = getattr(subtable, "ExtSubTable", subtable)
        for first, entries in getattr(subtable, "ligatures", {}).items():
            for entry in entries:
                name = "".join(inverse.get(glyph, "?") for glyph in [first, *entry.Component])
                ligatures[name] = entry.LigGlyph
names = set()
for file in ROOT.glob("*.py"):
    names.update(re.findall(r":material/(\w+):", file.read_text()))
names.update(["expand_more", "expand_less", "chevron_left", "chevron_right", "arrow_drop_down", "arrow_drop_up", "close", "check", "menu", "more_vert", "more_horiz", "arrow_back", "arrow_forward", "keyboard_arrow_down", "keyboard_arrow_up", "keyboard_arrow_left", "keyboard_arrow_right", "keyboard_double_arrow_left", "keyboard_double_arrow_right", "info", "warning", "error", "help", "search", "download", "upload", "file_download", "file_upload", "open_in_new", "content_copy", "fullscreen", "fullscreen_exit", "refresh", "visibility", "visibility_off", "settings", "calendar_today", "today", "undo", "redo", "delete", "add", "remove", "check_circle", "cancel", "done", "code", "terminal", "link", "play_arrow", "stop", "share", "save", "description", "folder", "folder_open", "tune", "sort", "arrow_upward", "arrow_downward", "check_small", "close_small", "first_page", "last_page", "unfold_more", "unfold_less"])
glyphs = font.getGlyphSet()
icons = {}
for name in sorted(names):
    if name not in ligatures:
        continue
    pen = SVGPathPen(glyphs)
    glyphs[ligatures[name]].draw(pen)
    icons[name] = pen.getCommands()
code = "const LAB_ICON_PATHS = " + json.dumps(icons, separators=(",", ":")) + ";\n"
code += r'''(() => {
  const fallback = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="7" fill="white"/></svg>';
  function update() {
    for (const element of document.querySelectorAll('[translate="no"][aria-hidden="true"]')) {
      const name = element.textContent.trim();
      if (!/^[a-z][a-z_0-9]*$/.test(name) || element.dataset.laIcon === name) continue;
      const path = LAB_ICON_PATHS[name];
      const svg = path ? '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 960"><path fill="white" transform="translate(0 960) scale(1 -1)" d="' + path + '"/></svg>' : fallback;
      const mask = 'url("data:image/svg+xml,' + encodeURIComponent(svg) + '")';
      element.style.setProperty('-webkit-mask-image', mask);
      element.style.setProperty('mask-image', mask);
      element.dataset.laIcon = name;
    }
  }
  let scheduled = false;
  const observer = new MutationObserver(() => {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => { scheduled = false; update(); });
  });
  observer.observe(document.body, {childList: true, subtree: true, characterData: true});
  update();
})();
'''
(ROOT / ".streamlit/static/pwa-icons.js").write_text(code)
license_text = "\n\n".join(str(font["name"].getDebugName(index) or "") for index in [0, 13, 14])
(ROOT / ".streamlit/static/assets/MATERIAL_SYMBOLS_LICENSE.txt").write_text(license_text)
print(f"{len(icons)} lokale SVG-Symbole erzeugt")
