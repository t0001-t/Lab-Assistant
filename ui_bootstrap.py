"""Lokale Styles und SVG-Symbole, ohne PWA-Gateway oder externe Abrufe."""
from functools import lru_cache
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


@lru_cache(maxsize=1)
def standalone_ui_assets() -> tuple[str, str]:
    """Dieselben lokalen UI-Dateien wie beim PWA-Gateway, ohne Netzabruf."""
    root = Path(__file__).resolve().parent / ".streamlit" / "static"
    return (
        (root / "pwa-ui.css").read_text(encoding="utf-8"),
        (root / "pwa-icons.js").read_text(encoding="utf-8"),
    )

def inject_ui() -> None:
    ui_css, icon_script = standalone_ui_assets()
    st.markdown("<style>" + ui_css + "</style>", unsafe_allow_html=True)
    icon_bootstrap = """
    <script>
    (() => {
      try {
        const document = window.parent.document;
        if (document.querySelector('script[src^="/pwa-icons.js"]') ||
            document.documentElement.dataset.labInlineIcons) return;
        document.documentElement.dataset.labInlineIcons = "ready";
        const MutationObserver = window.parent.MutationObserver;
        const requestAnimationFrame = window.parent.requestAnimationFrame.bind(window.parent);
    """ + icon_script + """
      } catch (error) { console.warn('[Lab UI] Symbole konnten nicht geladen werden:', error); }
    })();
    </script>
    """

    components.html(icon_bootstrap, height=0, width=0)
